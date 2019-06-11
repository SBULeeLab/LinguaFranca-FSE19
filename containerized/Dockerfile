# Use an official Ubuntu 16.04 runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /davis-fse19-artifact
WORKDIR /davis-fse19-artifact

# Run as root
USER root

# Scripts that access other scripts need to know where to look.
ENV ECOSYSTEM_REGEXP_PROJECT_ROOT /davis-fse19-artifact/LinguaFranca-FSE19
ENV VULN_REGEX_DETECTOR_ROOT /davis-fse19-artifact/LinguaFranca-FSE19/analysis/performance/vuln-regex-detector

# I have no clue why this is needed to compile Weideman's Java code.
ENV JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF8

# Prep instance.
# Why don't some of these work by default? Some kind of PATH issue?
RUN apt-get update && apt-get install -y git sudo wget curl bash vim sed less

# Fetch source from GitHub
RUN git clone https://github.com/VTLeeLab/LinguaFranca-FSE19

# Prep the local version.
WORKDIR /davis-fse19-artifact/LinguaFranca-FSE19
RUN ./configure.sh
