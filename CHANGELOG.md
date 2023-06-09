# ConfigTUI Changelog

### [1.2.5] - 2023-06-09
- Going forward from `v1.2`, the depedency is changed to `ruamel.yaml` instead `PyYAML`
- Increased IO speeds with the help of in-memory cache
- Added ability to preserve comments in the yaml file
- Fixed active node after a delete/insert operation
- Added native support for json files, and supports any configuration which can be loaded as json
- Fixed maintaining same positions when keys are edited

### [1.1] - 2023-06-06
- Added highlighter to show changes [update/insert/delete]
- Code optimizations under the hood for better performance

### [1.0] - 2023-06-05
- Added options to add / delete nodes
- Added CLI options

### [0.9] - 2023-06-01
- First version with support to view & edit yaml files
