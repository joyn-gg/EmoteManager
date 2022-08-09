//-- Package Declaration -------------------------------------------------------------------------------------------------------

package daemon

//-- Imports -------------------------------------------------------------------------------------------------------------------
import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"sync"
	"syscall"
	"time"

	"github.com/gofrs/uuid"
)

//-- Types ---------------------------------------------------------------------------------------------------------------------

type StatusSignalListener chan StatusSignal
type StatusSignal struct {
	DaemonID int
	Code     statusCode
}

type EventResponseCode int
type EventResponse struct {
	Code    EventResponseCode
	Message string
	Request struct {
		DaemonID int
		ID       uuid.UUID
		Code     EventCode
	}
}

type EventResponseListener chan EventResponse

type EventCode int
type Event struct {
	id           uuid.UUID
	code         EventCode
	responseSink EventResponseListener
}

type EventListener chan Event

type statusCode int
type Daemon struct {
	id     int
	status statusCode

	waitGroup *sync.WaitGroup

	eventListener EventListener
	statusSink    StatusSignalListener

	internals struct {
		ctx context.Context
		log *log.Logger

		lastEventTime            time.Time
		consecutiveEventFailures int
	}

	command struct {
		current            *exec.Cmd
		commandConstructor func() *exec.Cmd

		exitListener        chan string
		unexpectedExitCount int

		startWaitDuration time.Duration
		stopWaitDuration  time.Duration

		//TODO: It's possible to stream log files and look for heartbeats, killing when those stop automagically
		//heartbeatTimeoutDuration time.Duration
		//heartBeatPattern regexp.Regexp
		//lastHeartbeat time.Time
	}
}

//-- Shared Variables ----------------------------------------------------------------------------------------------------------
const (
	EventRequestStart EventCode = iota
	EventRequestRestart
	EventRequestStop
	EventRequestExit
)

const (
	EventResponseSuccess EventResponseCode = iota
	EventResponseFailure
	//EventResponseDead     //NOTE: Intended to be used if the reactor kept running to indicate a permanently dead state, no longer needed but left for conceptual reasons
)

const (
	StatusInitialized statusCode = iota
	StatusRunning
	StatusStopped
	StatusExited
	StatusDead
)

const (
	eventWaitTimer           = 5 * time.Second
	eventMaximumFailureCount = 3

	eventListenerBuffer = 5

	eventMaximumUnexpectedExitCount = 10
)

//-- Exported Functions --------------------------------------------------------------------------------------------------------

func NewDaemon(id int, ctx context.Context, logSink *os.File, waitGroup *sync.WaitGroup, statusSink StatusSignalListener, executable string, environment []string, args []string, startWaitDuration time.Duration, stopWaitDuration time.Duration) (*Daemon, error) {
	//-- Parameter checking ----------
	if len(executable) == 0 {
		return nil, fmt.Errorf(`missing or invalid value for required parameter: 'command'`)
	}

	//-- Create logger ----------
	var logger log.Logger
	{
		logger.SetOutput(logSink)
		logger.SetPrefix(fmt.Sprintf(`daemon (id: %d) `, id))
		logger.SetFlags(log.Ldate | log.Ltime)
	}

	//-- Create command constructor ----------
	var constructor = func() *exec.Cmd {
		var cmd *exec.Cmd
		cmd = exec.CommandContext(ctx, executable, args...)
		cmd.Env = environment

		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		return cmd
	}

	//-- Return assembled Daemon ----------
	var d = &Daemon{
		id:        id,
		status:    StatusInitialized,
		waitGroup: waitGroup,

		eventListener: make(EventListener, eventListenerBuffer),
		statusSink:    statusSink,

		internals: struct {
			ctx context.Context
			log *log.Logger

			lastEventTime            time.Time
			consecutiveEventFailures int
		}{
			ctx:                      ctx,
			log:                      &logger,
			lastEventTime:            time.Now(),
			consecutiveEventFailures: 0,
		},
		command: struct {
			current             *exec.Cmd
			commandConstructor  func() *exec.Cmd
			exitListener        chan string
			unexpectedExitCount int
			startWaitDuration   time.Duration
			stopWaitDuration    time.Duration
		}{
			current:            constructor(),
			commandConstructor: constructor,
			exitListener:       make(chan string, 1),
			startWaitDuration:  startWaitDuration,
			stopWaitDuration:   stopWaitDuration,
		},
	}
	d.updateStatus(StatusInitialized)
	return d, nil
}

func (d *Daemon) Start(ctx context.Context) error {
	//-- Protect against re-starting a dead Daemon (something is wrong) ----------
	if d.status != StatusInitialized {
		return fmt.Errorf(`daemon is outside of the initialized state and cannot be started in this way, use the event stream instead`)
	}

	//-- Queue a process start event ----------
	go func() { d.eventListener <- *NewDaemonEvent(EventRequestStart, nil) }()

	//-- Begin reactor loop ----------
	d.internals.log.Printf(`reactor start`)
	d.waitGroup.Add(1)

EventLoop:
	for {
		//-- Exit on repeated failures to prevent larger issues ------------
		if d.internals.consecutiveEventFailures > eventMaximumFailureCount {
			d.internals.log.Printf(`maximum event failure count reached, daemon will now die...`)
			d.updateStatus(StatusDead)
			break EventLoop
		}

		//-- Exit on repeated unexpected exists to prevent larger issues ----------
		if d.command.unexpectedExitCount > eventMaximumUnexpectedExitCount {
			d.internals.log.Printf(`maximum unexpected exit count reached, daemon will now die...`)
			d.updateStatus(StatusDead)
			break EventLoop
		}

		d.updateStatus(StatusRunning)

		//-- Listen to all inputs ----------
		select {

		//-- React to unexpected command exits ----------
		case result := <-d.command.exitListener:
			if d.status == StatusStopped || d.status == StatusDead {
				d.internals.log.Printf(`command has reported an expected exit code %v, daemon is stopped|dead`, result)
			} else {
				d.command.unexpectedExitCount = d.command.unexpectedExitCount + 1
				if alive, _ := d.commandIsAlive(); !alive {
					d.internals.log.Printf(`command has reported an unexpected exit Code %v, rebuilding and queueing a restart`, result)
					d.command.current = d.command.commandConstructor()
					d.eventListener <- Event{code: EventRequestStart}
				} else {
					d.internals.log.Printf(`command has reported an unexpected exit Code %v but is still alive...trying a restart?`, result)
					d.eventListener <- Event{code: EventRequestRestart}
				}
			}

		//-- React to consumer requests ----------
		case event := <-d.eventListener:
			switch event.code {
			case EventRequestStart:
				d.handleEventResponse(event, d.commandStart())
			case EventRequestRestart:
				d.handleEventResponse(event, d.commandRestart())
			case EventRequestStop:
				d.handleEventResponse(event, d.commandStop())
				d.updateStatus(StatusStopped) //NOTE: I deliberately do not break here because this was a planned operation, and we should plan on executing further events
			case EventRequestExit:
				d.handleEventResponse(event, d.commandStop())
				break EventLoop
			}

		//-- React to context closure ----------
		case <-ctx.Done():
			d.internals.log.Printf(`context has expired, shutting down`)
			break EventLoop
		}

		d.internals.lastEventTime = time.Now()
		d.waitWithContext(eventWaitTimer)
	}

	//-- Update status ----------
	if d.status != StatusDead {
		d.updateStatus(StatusExited)
	}

	//-- Ensure sub-process exit (shouldn't really be required with the attached context) ----------
	if alive, _ := d.commandIsAlive(); alive {
		d.internals.log.Printf(`command is still running, attempting a graceful-ish shut down...`)

		if stopErr := d.commandStop(); stopErr != nil {
			d.waitGroup.Done()
			return stopErr
		}
	}

	d.waitGroup.Done()
	return nil
}

func (d Daemon) ID() int {
	return d.id
}

func (d Daemon) EventListener() EventListener {
	return d.eventListener
}

func NewDaemonEvent(code EventCode, responseSink EventResponseListener) *Event {
	var event = &Event{
		id:           uuid.UUID{},
		code:         code,
		responseSink: responseSink,
	}

	if id, err := uuid.NewV4(); err == nil {
		event.id = id
	}
	return event
}

//-- Internal Functions --------------------------------------------------------------------------------------------------------
func (d Daemon) waitWithContext(dur time.Duration) {
	select {
	case <-time.After(dur):
		return
	case <-d.internals.ctx.Done():
		return
	}
}

func (d Daemon) updateStatus(status statusCode) {
	d.status = status

	if d.statusSink != nil {
		d.statusSink <- StatusSignal{
			DaemonID: d.id,
			Code:     d.status,
		}
	}
}

func (d *Daemon) handleEventResponse(event Event, result error) {
	//-- Handle response creation and internal failure counter ----------
	var response EventResponse
	if result == nil {
		d.internals.consecutiveEventFailures = 0
		response = EventResponse{
			Code:    EventResponseSuccess,
			Message: `operation successful`,
		}
	} else {
		d.internals.consecutiveEventFailures = d.internals.consecutiveEventFailures + 1
		response = EventResponse{
			Code:    EventResponseFailure,
			Message: result.Error(),
		}
	}

	//-- Send response (if channel is provided) ---------
	if event.responseSink != nil {
		if result == nil {
			event.responseSink <- response
		} else {
			event.responseSink <- response
		}
	}
}

func (d *Daemon) commandIsAlive() (bool, error) {
	if d.command.current.Process == nil {
		return false, fmt.Errorf(`command is null`)
	} else if err := d.command.current.Process.Signal(syscall.Signal(0)); err != nil {
		return false, err
	} else if (d.command.current.ProcessState != nil) && (d.command.current.ProcessState.Exited() == true) {
		return false, fmt.Errorf(`command state exists and is marked as 'exited'`)
	}

	return true, nil
}

func (d *Daemon) commandStart() error {
	if alive, _ := d.commandIsAlive(); alive {
		return nil //No action needed
	} else if err := d.command.current.Start(); err != nil {
		return fmt.Errorf(`unexpected error starting command: %s`, err.Error())
	} else {
		//-- Execute Wait(), notifying and releasing on exit ---------
		go func() {
			var err = d.command.current.Wait()
			if err != nil {
				if execErr, ok := err.(*exec.ExitError); ok {
					d.command.exitListener <- execErr.Error()
				} else {
					d.command.exitListener <- `unknown error condition`
				}
			} else {
				d.command.exitListener <- `normal exit`
			}
		}()
	}

	d.waitWithContext(d.command.startWaitDuration)
	if alive, _ := d.commandIsAlive(); !alive {
		return fmt.Errorf(`unexpected error command has not started`)
	}
	return nil
}

func (d *Daemon) commandRestart() error {
	if err := d.commandStop(); err != nil {
		return fmt.Errorf(`unexpected error stopping command during restart: %d`, err)
	} else if err := d.commandStart(); err != nil {
		return fmt.Errorf(`unexpected error starting command during restart: %d`, err)
	}
	return nil
}

func (d *Daemon) commandStop() error {
	if alive, _ := d.commandIsAlive(); !alive {
		return nil //No action needed
	} else if termErr := d.command.current.Process.Signal(syscall.SIGTERM); termErr != nil {
		d.internals.log.Printf(`unexpected error interrupting command (code: %s) waiting for a moment, then killing`, termErr.Error())

		d.waitWithContext(d.command.stopWaitDuration)
		if killErr := d.command.current.Process.Signal(syscall.SIGKILL); killErr != nil {
			return fmt.Errorf(`unexpected error killing command (code: %s), unable to stop`, killErr.Error())
		}
	}

	d.waitWithContext(d.command.stopWaitDuration)
	if alive, _ := d.commandIsAlive(); alive {
		return fmt.Errorf(`unexpected error command has not stopped`)
	}
	return nil
}
