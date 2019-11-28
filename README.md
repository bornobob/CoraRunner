# CoraRunner
Small Python framework to test Cora and generate HTML results

# How to run
## CoraRunner
The CoraRunner (`main.py`) should be called as follows:  
```bash
python main.py <settings file> <test files directory> <output file>
```
The settings file should be a file in `.json` format containing the following keys:
- `cora-path`: the path to the cora `.jar`
- `java-path`: the path to the java executable
- `configs`: a dictionary with the following keys:
  - `techniques`: the techniques you want to run
  - `semi_unifiers`: the semi unifiers to run
  - `max_unfoldings`: the maximum number of unfoldings te techniques may do
  - `timings`: the timeouts to run
  - `augment`: whether or not to augment the TRS as preprocessing  
 - The configs will all be executed on all files, with all combinations of techniques, semi-unifiers, max-unfoldings, timings and augments.  

The `<test files directory>` may contain TRS in `.trs`, `.mstrs` and `.cora` format.  
The `<output file>` may not exist, and will be formatted as follows:
```
[
  <Result>
]
```

`Result`:
```
{
  "file": the executed file,
  "config": {
    "technique": the executed technique,
    "semi_unifier": the semi-unifier used,
    "max_unfoldings": the max-unfoldings used,
    "timing": the timeout used,
    "augment": whether or not the trs was augmented
  },
  "result": {
    "result_type": result of the run,
    "cora_time": time in ms measured by cora,
    "cpu_time": time in ms measured by the runner,
    "error": (possibly null) error from cora
  }
}
```

## HTMLGenerator
The HTMLGenerator accepts a result in the format described above, and generates a simple HTML page with the results in a table. 
The HTMLGenerator (`htmlgenerator.py`) should be called as follows:  
```bash
python htmlgenerator.py <results file> <output file>
```
The `<results file>` should be formatted as described in the previous section.  
The `<output file>` will be an html file with the results from the results file and may not exist yet.
