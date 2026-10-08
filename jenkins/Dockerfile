# Jenkins for LabLend: pipeline plugins + Docker CLI, configured as code.
FROM jenkins/jenkins:lts-jdk21

USER root
# Docker CLI + Compose plugin so pipeline stages can build and deploy containers
COPY --from=docker:27.5.1-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:27.5.1-cli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

USER jenkins
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY --chown=jenkins:jenkins casc.yaml /usr/share/jenkins/ref/casc.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false" \
    CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
