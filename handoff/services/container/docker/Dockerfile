# Pull base image.
FROM public.ecr.aws/m5u3u5p2/handoff-base:0.1

MAINTAINER Daigo Tanaka <daigo.tanaka@gmail.com>

COPY . /app/
RUN chmod 777 -R /app

WORKDIR /app

RUN ./script/install_handoff

# It is recommended to make virtual envs for each process
RUN handoff workspace install -p project -w workspace

# Make sure to delete these directories in case sensitive information was accidentally copied.
RUN rm -fr project
RUN rm -fr workspace/config
RUN rm -fr workspace/files
RUN rm -fr workspace/artifacts

RUN chmod a+x /usr/local/bin/*

ENTRYPOINT [ "/tini", "--" ]
CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"dev"} -a
