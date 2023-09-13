# Motivation Study

## How we filter bug reports?

### A. Filtering to get crash report
Not all bug reports submitted by testers to developers are crash reports, there are also some minor issues such as displaying bug reports, features that need to be added, etc. These minor reports are out of the scope of our study.

We filter the crash reports by keywords (crash, stop, and exception) and get a total of 10843 crash reports.

### B. Filtering to get crash reports with reproducing steps
Crash reports that satisfy the following two conditions are considered to contain reproducing steps:

1. Containing at least one of the following verbs that indicate GUI operations:`['select', 'choose', 'swipe', 'press', 'type', 'enter', 'open', "insert", "rotate", 'tap', 'click', 'go', 'write', 'input']`
2. Containing markers indicating the sequence of steps: `"-", ">", "1.XX, 2.XX`

By using the above two conditions, we filter out 5981 crash reports that containing reproducing steps.

### C. Filtering to get crash reports with the crash stack trace
Crash reports that at least a line that satisfy the following pattern are considered to contain crash the stack trace: `r".*?\.java:\d+.*?"`

By using the above two conditions, we filter out 3566 crash reports that containing the crash stack trace.