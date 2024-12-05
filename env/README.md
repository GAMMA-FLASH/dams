# gammaflash-env
gammaflash-env

## Install and run the environment

1. Install python3 (current supported version 3.8.8)

2. Create the environment

    ```
    python3 -m venv /path/to/new/virtual/environment
    ```

3. Install requirements

    ```
    pip install -r venv/requirements.txt
    ```

4. Run the activate script

    ```
    source /path/to/new/virtual/environment/bin/activate
    ```

---

## Docker image

* Build the image
    ```
    docker build -t dams_image:1.6.0 .
    ```

* Run container (without `--rm` for not auto-remove container after disconnection)
    ```
    docker run --rm -it -v /Users/riccardofalco/Downloads/dams:/home/gamma/workspace/dams  -v /Users/riccardofalco/Downloads/Data/DL0:/home/gamma/workspace/Data/DL0  -v /Users/riccardofalco/Downloads/Data/DL1:/home/gamma/workspace/Data/DL1 -v /Users/riccardofalco/Downloads/Data/DL2:/home/gamma/workspace/Data/DL2 -v /Users/riccardofalco/Downloads/Out/json:/home/gamma/workspace/Data/Out/json -v /Users/riccardofalco/Downloads/Out/logs:/home/gamma/workspace/Data//Out/logs --name dams_cont dams_image:latest /bin/bash
    ```