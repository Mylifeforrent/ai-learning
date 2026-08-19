# Getting started

Acme SDK helps Python applications send events to the Acme platform.

## Installation

Python 3.11 or newer is required.

Install the package:

```bash
pip install acme_sdk
```

After installing, create a client:

```python
from acme_sdk import AcmeClient

client = AcmeClient(api_key="your-api-key")
```

See the [configuration guide](configuration.md) for environment setup and API key options.
