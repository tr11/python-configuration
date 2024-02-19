# Contributing to python-configuration

First off, thanks for taking the time to contribute!

## Setting up a dev environment

1. Fork the [`tr11/python-configuration`](https://github.com/tr11/python-configuration) GitHub repo.
1. Clone the fork:

    ```shell
    git clone https://github.com/<your_username>/python-configuration.git
    cd python-configuration
    ```

1. Use [`hatch`](https://hatch.pypa.io/) to generate a version file and install the dependencies

```shell
hatch build --hooks-only  # generate a version file from the git commit
# or
hatch build
```

### Running the tests

To run the tests (which include linting and type checks), run:
```shell
hatch run test:test 
```

Before opening a PR, make sure to run 
```shell
hatch run testing:test 
```
which executes the previous test command on all Python versions supported by the library.
