# solid_client

![GitHub Actions (Tests)](https://github.com/hamishgibbs/solid_client/workflows/Tests/badge.svg)
[![codecov](https://codecov.io/gh/hamishgibbs/solid_client/branch/master/graph/badge.svg)](https://codecov.io/gh/hamishgibbs/solid_client)


An example [Solid](https://solidproject.org/) client implemented in Python.

**Please note:** This library is in the early stages of development. There are no guarantees of security or conformance with the draft [SOLID-OIDC](https://solid.github.io/authentication-panel/solid-oidc/) specification. The library is intended as an example implementation of client authentication in the SOLID ecosystem.

## See Also

This library is being developed alongside example implementations of:

* [Solid Identity Provider (IdP)](https://github.com/hamishgibbs/solid_idp).
* [Solid Resource Server (RS)](https://github.com/hamishgibbs/solid_server).

### Installation

**From a clone:**

To develop this project locally, clone it onto your machine:

```shell
git clone https://github.com/hamishgibbs/solid_client.git
```

Enter the project directory:

```shell
cd solid_client
```

Install the package with:

```shell
pip install .
```

**From GitHub:**

To install the package directly from GitHub run:

```shell
pip install git+https://github.com/hamishgibbs/solid_client.git
```

## Usage

The API is configured in `solid_client/main.py`. To start the development server, initiate the server with `uvicorn`.

``` shell
uvicorn solid_client.main:app --reload --port 8001
```

The current implementation assumes that the IdP is available at http://127.0.0.1:8000/, the Client is available at http://127.0.0.1:8001/, and the RS is available at http://127.0.0.1:8002/.

## Contributions

This library is in the early stages of development and is intended to demonstrate the flow of Solid client authentication. Review, contributions, and discussion are welcome.

## Acknowledgements

This library relies on draft SOLID specifications authored by the [Solid Project](https://solidproject.org/).
