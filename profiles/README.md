# Client profiles

Each real client gets one directory here, for example `profiles/lucy/`.

That directory holds their `profile.json`, resume, tracker (`jobs/`), and generated digest (`output/`). It is gitignored. Do not copy one client's files into another client's directory.

The committed sample is `examples/sample-client/`. It is synthetic. Start a real profile with:

```text
job-agent init --profile lucy
```

Or copy the sample layout:

```text
job-agent init --profile lucy --from examples/sample-client
```

Then replace every sample fact before the first real search.
