# emote_manager

[![Lint](https://github.com/tournament-kings/emote_manager/actions/workflows/lint.yml/badge.svg)](https://github.com/tournament-kings/emote_manager/actions/workflows/lint.yml)
[![ci/cd](https://github.com/tournament-kings/emote_manager/actions/workflows/ci.yml/badge.svg)](https://github.com/tournament-kings/emote_manager/actions/workflows/ci.yml)


If you're looking for the latest non-production code, you probably want
the [staging](https://github.com/tournament-kings/emote_manager/tree/staging) branch.

## Setup

### Windows

#### Requirements to setup the bot locally:

Install [Docker](https://docs.docker.com/docker-for-windows/install/)

Download the [latest Linux Kernel](https://docs.microsoft.com/en-us/windows/wsl/wsl2-kernel)

Install the [Ubuntu Terminal](https://ubuntu.com/wsl)

#### Getting WLS and Ubuntu synced

Open up CMD and run the following commands:

```wsl.exe --set-version ubuntu 2 && wsl.exe --set-default-version 2 && wsl --set-default ubuntu```

This will set your Ubuntu Terminal to run in WLS2, and also setting future default versions to WLS2. The final command
sets Ubuntu as the default WSL. So when you open up WSL, it'll be running the Ubuntu Terminal rather than the standard
WLS.

#### Getting Ubuntu and Docker synced

Open up Docker and let it start up correctly, you may need to restart.

Click on the Settings cog, go to Resources then WSL Integration

Enable integration with default WSL distro, and you should also see Ubuntu beneath it under 'Enable integration with
additional distros'. Give that box a tick as well (You may need to hit 'Refresh').

Once done, click 'Apply & Restart'

#### Ubuntu Terminal

Set up your Ubuntu Terminal with a username and password

#### Follow the Linux Tutorial

---

### Linux

#### Requirements to setup the bot locally:

docker (install via: `sudo apt install docker` | `sudo pacman -S docker`)

jq     (install via: `sudo apt install jq`     | `sudo pacman -S jq`)

##### You will also need:

Discord Developer Application: for a Bot Token

#### Clone both of the following repositories:

[database_manager](https://github.com/tournament-kings/database_manager)

[emote_manager](https://github.com/tournament-kings/emote_manager)

#### Switch to the appropriate branch on BOTH repositories:

Example: `git checkout staging`

#### In database_manager:

Create a Directory in `./database_manager/config/secrets` called `development`

Copy the content of `./database_manager/config/secrets/example` across to your `development` directory

Adjust your JSON file named `script_secrets.json` to point to the correct schema

#### In emote_manager:

Create a Directory in `./emote_manager/config/secrets` called `development`

Copy the content of `./emote_manager/config/secrets/example` across to your `development` directory

Adjust your JSON file named `script_secrets.json` replacing all the `example_x` with correct values

## Startup

Run docker: `dockerd`

In database_manager run: `./scripts/migrate development`

*You may need to run this twice, first time make refuse connection*

Wait until the database image builds and migrates.

In emote_manager run: `./scripts/run development`

---

#### Windows Troubleshoot

##### CMount

If you are receiving an error in docker with using the cmount, run the following commands:

```sudo mkdir /sys/fs/cgroup/systemd```

```sudo mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/systemd```

---

## Links

 - [Software Lifecycle](https://youtrack.tk-internal.com/articles/ENG-A-3/Software-Lifecycle)
 - [Style Guide: Python](https://youtrack.tk-internal.com/articles/ENG-A-29/Python)
