# Use the specified base image
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel

# Set environment variable to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list
RUN apt-get update -y

# Install git
RUN apt-get install -y git

# Install Python packages using pip
RUN git clone https://github.com/jkobject/scprint .
RUN cd scprint
RUN pip install -e ".[flash,dev]"
RUN lamin init --storage ./main --name main --schema bionty
RUN python -c 'import bionty as bt; bt.base.reset_sources(); bt.core.sync_all_sources_to_latest()'
RUN lamin load main
RUN python -c 'from scdataloader.utils import populate_my_ontology; populate_my_ontology()'

# Set the default command (can be overridden)
CMD ["scprint", "--help"]

# to install the nvidia-cuda-toolkit
# curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
# sudo apt-get update
# sudo apt-get install -y nvidia-container-toolkit