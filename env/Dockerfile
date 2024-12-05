FROM oraclelinux:8 AS oracle8

# ---------------------------------- Installing dependencies as root ---------------------------------- 
RUN dnf install -y epel-release git cmake3 gcc-c++ gcc binutils \
compat-openssl10 libX11-devel libXpm-devel libXft-devel libXext-devel \ 
gsl-devel openssl-devel wget bzip2-devel libffi-devel xz-devel sqlite-devel \
ncurses ncurses-devel make xz libzstd libzstd-devel which rsync \
nmap-ncat chrony

RUN dnf install -y oracle-epel-release-el8
RUN dnf config-manager --enable ol8_codeready_builder
RUN dnf install -y hdf5 hdf5-devel

# ---------------------------------- Create Gamma user ---------------------------------- 
USER root 
RUN useradd gamma
USER gamma
WORKDIR /home/gamma
RUN mkdir -p /home/gamma/dependencies
SHELL ["/bin/bash", "--login", "-c"]

USER root 

COPY venv /home/gamma/dependencies/gamma-env

# Define architecture-specific environment variables
# Handle architecture detection, requirements, and Miniconda in a single RUN
RUN ARCH=$(uname -m) &&                                         \
    if [ "$ARCH" = "x86_64" ]; then                             \
        echo "Configuration for AMD64";                         \
        # Insert specific commands for x86_64 (AMD64) here
        MINICONDA=Miniconda3-latest-Linux-x86_64.sh;            \
        REQUIREMENTS=requirements.amd.txt;                      \
    elif [ "$ARCH" = "aarch64" ]; then                          \
        echo "Configuration for ARM64";                         \
        # Insert specific commands for ARM64 here
        MINICONDA=Miniconda3-latest-Linux-aarch64.sh;           \
        REQUIREMENTS=requirements.arm.txt;                      \
    else                                                        \
        echo "Unsupported architecture: $ARCH"; exit 1;         \
    fi &&                                                       \
    echo "Using Miniconda installer: $MINICONDA" &&             \
    wget https://repo.anaconda.com/miniconda/$MINICONDA &&      \
    chmod +x $MINICONDA &&                                      \
    ./$MINICONDA -b -p /opt/conda &&                            \
    rm $MINICONDA &&                                            \
    pwd &&                                                      \
    mv /home/gamma/dependencies/gamma-env/$REQUIREMENTS /home/gamma/dependencies/gamma-env/requirements.txt


WORKDIR /home/gamma
RUN chown -R gamma:gamma /home/gamma/

RUN mkdir -p /home/gamma//dependencies/gamma-env 
COPY conda/environment.yml /home/gamma/dependencies/gamma-env
#COPY venv/$REQUIREMENTS gamma-env

USER gamma

RUN export PATH=$PATH:/opt/conda/bin && conda config --append channels conda-forge && conda config --set channel_priority strict &&  conda env create -n gammaenv -f /home/gamma/dependencies/gamma-env/environment.yml

RUN export PATH=$PATH:/opt/conda/bin && source activate gammaenv && cd /home/gamma/dependencies/gamma-env && pip3 install -r /home/gamma/dependencies/gamma-env/requirements.txt

# ---------------------------------- Install RTA-DATAPROCESSOR ---------------------------------- 
RUN git clone https://github.com/ASTRO-EDU/rta-dataprocessor.git && \
    mv /home/gamma/rta-dataprocessor /home/gamma/dependencies/rta-dataprocessor 

USER root
RUN  mkdir /home/gamma/workspace &&   \
     mkdir /home/gamma/workspace/Data 
RUN chown -R gamma:gamma /home/gamma/workspace/Data
COPY ./entrypoint.sh /home/gamma/entrypoint.sh

RUN chmod +x /home/gamma/entrypoint.sh

USER gamma
ENV PATH="/opt/conda/bin:$PATH"

ENV PYTHONPATH="/home/gamma/dependencies/rta-dataprocessor/workers"
ENV PYTHONPATH="${PYTHONPATH}:/home/gamma/workspace"
ENV PYTHONPATH="${PYTHONPATH}:/home/gamma/workspace/dams/dl1"
ENV PYTHONPATH="${PYTHONPATH}:/home/gamma/workspace/dams/dl2"
ENV PYTHONPATH="${PYTHONPATH}:/home/gamma/workspace/dams/pipe"

# ENTRYPOINT ["/bin/bash", "-c", "source /home/gamma/entrypoint.sh && exec bash"]
# CMD ["/bin/bash", "-c", "source /home/gamma/entrypoint.sh && exec bash"]
RUN echo "source /opt/conda/bin/activate gammaenv" >> /home/gamma/.bashrc
