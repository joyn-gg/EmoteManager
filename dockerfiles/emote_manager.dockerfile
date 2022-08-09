#-- Build base image -----------------------------------------------------------------------------------------------------------
FROM alpine:3 AS entrypoint_building_environment

# Install tools
RUN apk --no-cache update && \
    apk --no-cache upgrade

RUN apk --no-cache add git go

# Set working directory
WORKDIR /usr/src/go_shard

# Copy source files
COPY ./entrypoint ./

# Install dependencies
RUN go get -d ./...

# Build targets
RUN go build -ldflags '-extldflags "-static"' -o go_shard

#-- Build base image -----------------------------------------------------------------------------------------------------------
FROM python:3.8-alpine AS dependency_solving_environment

# Set timezone to UTC by default
RUN ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime

# Use unicode
ENV LANG=C.UTF-8

# Install tools
RUN apk --no-cache update && \
    apk --no-cache upgrade

RUN apk --no-cache add gcc imagemagick imagemagick-dev musl-dev

# Set working directory
ARG WORKING_DIRECTORY=/opt/src/project
RUN mkdir --parents ${WORKING_DIRECTORY}
WORKDIR ${WORKING_DIRECTORY}

# Download python modules
COPY requirements.txt ${WORKING_DIRECTORY}
RUN pip3 install -r requirements.txt

#-- Build build context image --------------------------------------------------------------------------------------------------
FROM dependency_solving_environment AS build_context

# Set working directory
ARG WORKING_DIRECTORY=/opt/src/project
WORKDIR ${WORKING_DIRECTORY}

#Copy project code
COPY . ${WORKING_DIRECTORY}

#-- Run container ------------------------------------------------------------------------------------------------------------
FROM build_context AS run_context

# Copy entrypoint
COPY --from=entrypoint_building_environment /usr/src/go_shard/go_shard /usr/bin/go_shard

# Set working directory
ARG WORKING_DIRECTORY=/opt/src/project
WORKDIR ${WORKING_DIRECTORY}/bot

# Initialize / begin entrypoint
ENV DISCORD_TOKEN=default_value
ENV DISCORD_SHARDS_PER_PROCESS=default_value

ENV BOT_PREFIX=default_value
ENV BOT_VERSION=default_value
ENV BOT_LOG_LEVEL=default_value

ENV PYTHONPATH "${PYTHONPATH}:${WORKING_DIRECTORY}"

# Run bot
ENTRYPOINT ["/usr/bin/go_shard"]
