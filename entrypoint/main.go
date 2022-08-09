//-- Package Declaration -------------------------------------------------------------------------------------------------------
package main

//-- Imports -------------------------------------------------------------------------------------------------------------------
import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"go_shard/pkg/configuration"
	"go_shard/pkg/daemon"
	"go_shard/pkg/discord"
)

//-- Constants -----------------------------------------------------------------------------------------------------------------
const (
	daemonStartWaitDuration = 5 * time.Second

	daemonProcessStartWaitDuration = 60 * time.Second
	daemonProcessStopWaitDuration  = 60 * time.Second

	//daemonStartWaitDuration = 0 * time.Second
	//
	//daemonProcessStartWaitDuration = 1 * time.Second
	//daemonProcessStopWaitDuration  = 1 * time.Second

	eventListenerBuffer = 1_000
)

var (
	executable          = `/usr/local/bin/python3`
	executableArguments = []string{`__main__.py`}

	//executable          = `/bin/sleep`
	//executableArguments = []string{`15`}
)

//-- Types ---------------------------------------------------------------------------------------------------------------------

//-- Exported Functions --------------------------------------------------------------------------------------------------------
func main() {
	//-- Setup Logger ----------
	{
		log.SetOutput(os.Stdout)
		log.SetPrefix(fmt.Sprintf(`core(id: %d) `, 0))
		log.SetFlags(log.Ldate | log.Ltime)
	}

	//-- Generate process invocation commands ----------
	log.Printf(`generating command/environments...`)
	var executableEnvironments [][]string
	{
		if result, err := discord.GetDiscordShardEnvironments(
			configuration.Configuration().DiscordShardsPerProcess,
			configuration.Configuration().ParsedShardIDs(),
			*configuration.Configuration().DiscordToken,
		); err != nil {
			log.Fatalf(`unrecoverable error trying to make shard plan %s`, err.Error())
		} else {
			for _, group := range result {
				executableEnvironments = append(executableEnvironments, append(os.Environ(), group.Environment...))
			}
		}
	}

	//-- Setup application contexts and channels to be used in daemons ----------
	log.Printf(`creating master context and channels...`)
	var ctx, cancel = context.WithCancel(context.Background())
	var logSink = make(daemon.EventResponseListener, eventListenerBuffer)
	var daemonStatusSink = make(daemon.StatusSignalListener, eventListenerBuffer)

	//-- Create daemons en masse (with wait groups and signal channels) ----------
	log.Printf(`creating daemons...`)
	var waitGroup sync.WaitGroup
	var daemons []*daemon.Daemon
	for id, environment := range executableEnvironments {

		if result, err := daemon.NewDaemon(
			id,
			ctx,
			os.Stdout,
			&waitGroup,
			daemonStatusSink,
			executable,
			environment,
			executableArguments,
			daemonProcessStartWaitDuration,
			daemonProcessStopWaitDuration,
		); err != nil {
			log.Fatalf(`unrecoverable error while creating daemon: %s`, err.Error())
		} else {
			daemons = append(daemons, result)
		}

	}

	//-- Startup main reactors -----
	log.Printf(`starting infintie daemon event response log loop...`)
	go logDaemonEventResponses(ctx, &waitGroup, logSink)

	log.Printf(`starting infintie daemon status signal loop...`)
	go terminateOnDaemonDeadStateNotification(ctx, cancel, &waitGroup, daemonStatusSink)

	log.Printf(`starting infintie interrupt signal loop...`)
	go catchInterruptSignal(cancel)

	//-- Start daemons (in time delayed sequence) -----------
	log.Printf(`starting daemons(%d)...`, len(daemons))
	for _, subject := range daemons {
		var x = subject
		go func() {
			if err := x.Start(ctx); err != nil {
				log.Fatalf(`unexpected errror starting daemon (%d): %s`, x.ID(), err)
			} else {
				log.Printf(`started daemon (%d)`, x.ID())
			}
		}()
		time.Sleep(daemonStartWaitDuration)
	}

	//-- Wait for wait waitGroup ----------
	log.Printf(`started, waiting for wait waitGroup to empty...`)
	time.Sleep(3 * time.Second)
	waitGroup.Wait()

	//-- Exit ----------
	log.Printf(`exiting...`)
	time.Sleep(3 * time.Second)
	os.Exit(0)
}

//-- Internal Functions --------------------------------------------------------------------------------------------------------
func logDaemonEventResponses(ctx context.Context, group *sync.WaitGroup, sink daemon.EventResponseListener) {
	group.Add(1)
	for {
		select {
		case event := <-sink:
			if event.Code != daemon.EventResponseSuccess {
				log.Printf(`failed daemon (%d) event, response '%s' for event %v`, event.Code, event.Message, event.Request)
			}
		case <-ctx.Done():
			log.Printf(`master context was makred as 'done' breaking out of daemon event log loop`)
			group.Done()
			return
		}
	}
}

func terminateOnDaemonDeadStateNotification(ctx context.Context, cancel context.CancelFunc, group *sync.WaitGroup, sink daemon.StatusSignalListener) {
	group.Add(1)
	for {
		select {
		case event := <-sink:
			if event.Code == daemon.StatusExited || event.Code == daemon.StatusDead {
				log.Printf(`daemon (%d) has entered a terminal state, aborting the whole system`, event.DaemonID)
				cancel()
			}
		case <-ctx.Done():
			log.Printf(`master context was makred as 'done' breaking out of daemon event log loop`)
			group.Done()
			return
		}
	}
}

func catchInterruptSignal(cancel context.CancelFunc) {
	//-- Loop and listen for interrupts (forever) ----------
	var signalChannel = make(chan os.Signal, 1)
	signal.Notify(signalChannel, os.Interrupt, syscall.SIGTERM)

	var sig = <-signalChannel

	log.Printf(`signal (%d) intercepted, shutting down....`, sig)
	time.Sleep(3 * time.Second)

	//-- Invoke master context cancellation ----------
	cancel()
}
