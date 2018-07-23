# Hacking

## Tests

### Unit tests

Running unit tests:

```sh
$> tox
```

### UX scenarios

UX testing is supposed to provide end-user intuitive command-line interface for
Ansit, e.g.: readable error reports and predictable behaviour. Since it's not
tested automatically, there are a few example scenarios for testing it:

#### Faulty provider

```sh
$> ansit -m tests/examples/failing_drivers.yml --update up
```

```sh
$> ansit -m tests/examples/failing_drivers.yml --update destroy
```

#### Faulty provisioner

```sh
$> ansit -m tests/examples/failing_drivers.yml --update provision
```

#### Faulty tester

```sh
$> ansit -m tests/examples/failing_drivers.yml --update test
```

#### Faulty driver init

```sh
$> ansit -m tests/examples/failing_init.yml --update test
```
