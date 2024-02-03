##################################################
## "base" stage
##################################################

FROM docker.io/python:3.12-slim-bookworm AS base

ARG USER=oasch
ARG UID=49374
ARG HOME=/${USER}

RUN useradd -u "${UID:?}" -g 0 -md "${HOME:?}" "${USER:?}" \
	&& chmod -R g=u "${HOME:?}"

ENV PATH=${HOME}/.local/bin:${PATH}
WORKDIR ${HOME}

##################################################
## "build" stage
##################################################

FROM base AS build

RUN apt-get update && apt-get install -y make

USER ${UID}:0

RUN --mount=type=cache,uid=${UID},gid=0,dst=${HOME}/.cache/ \
	python -m venv --upgrade-deps ./.venv/

COPY --chown=${UID}:0 ./requirements*.txt ./
RUN --mount=type=cache,uid=${UID},gid=0,dst=${HOME}/.cache/ \
	./.venv/bin/python -m pip install -r ./requirements-dev.txt

COPY --chown=${UID}:0 ./ ./
RUN make all

##################################################
## "main" stage
##################################################

FROM base AS main

USER ${UID}:0

RUN --mount=type=bind,from=build,src=${HOME}/dist/,dst=/wheelhouse/ \
	--mount=type=cache,uid=${UID},gid=0,dst=${HOME}/.cache/ \
	python -m pip install /wheelhouse/*.whl \
	&& mkdir "${HOME:?}"/schemas/ \
	&& chmod -R g=u "${HOME:?}"

ENTRYPOINT ["./.local/bin/openapi2jsonschema"]
CMD ["--help"]
