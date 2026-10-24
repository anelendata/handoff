# Pull base image.
FROM public.ecr.aws/m5u3u5p2/handoff-base:0.2

# MAINTAINER Daigo Tanaka <daigo@anelen.co>

COPY . /app/

WORKDIR /app

# Keep chmod, install, and rm in one layer: a separate chmod layer would store
# a second copy of the project files, and a separate rm layer would only hide
# them from the final image, not remove them from the earlier layers.
# It is recommended to make virtual envs for each process
RUN chmod 777 -R /app && \
    ./script/install_handoff && \
    handoff workspace install -p project -w workspace && \
    rm -fr project workspace/config workspace/files workspace/artifacts

RUN chmod a+x /usr/local/bin/*

ENTRYPOINT [ "/tini", "--" ]
CMD handoff ${COMMAND:-run} -w workspace -a -v $(eval echo ${__VARS:-"dummy=1"}) -s ${HO_STAGE:-"dev"} -a
