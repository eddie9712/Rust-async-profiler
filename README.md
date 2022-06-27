# Rust-Async-Context-Tracer
- Understand the behavior of your asynchronous tasks and futures.    
▶️New branch for tokio-runtime is working in progress
## Prerequisite:
* Please install and build [uftrace](https://github.com/namhyung/uftrace) first
* Make sure using the **rust toolchain that supports `mcount` call** (the `mcount` flag is temporarily broken and see [here](https://github.com/namhyung/uftrace/issues/1392) for a workaround)  
and if the circumstances permit, you can just use the earlier toolchain (e.g. `nightly-2021-03-16-x86_64-unknown-linux-gnu`)
* Build your executable in **debug mode**  
In rust nightly build:
```
RUSTFLAGS="-Z instrument-mcount -C passes=ee-instrument,post-inline-ee-instrument" cargo build --bin $BINARY_NAME 
```
## What is a tracing tool for asynchronous rust?
* With this tool, we can:
   * Understand the behavior of rust asynchronous tasks, including the polling time of the futures and the waiting time of the futures
   * Find out some abnormal execution patterns (long polling time may cause [blocking](https://ryhl.io/blog/async-what-is-blocking/))
   * 
* e.g. Here is a simple rust asynchronous program:
```
use async_std::task;
use std::time::Duration;

async fn my_test()
{
   task::sleep(Duration::from_millis(100)).await;
}
#[async_std::main]
async fn main(){
     my_test().await;
     task::sleep(Duration::from_millis(150)).await;
}
```
And We can have a visualization for our rust asynchronous program:  
![image](https://user-images.githubusercontent.com/37073963/160838711-d5dd5d1f-84cc-417c-ad1d-88b59e968a04.png)
## Usage
* Clone the repository (No building needed) 
* Move the profile directory into your `target` directory
 ```
 profile
 ├── parser_nu.py
 ├── parser.py
 └── profile.sh
 ```
* Run the profiler script:  
For tracing all futures:
`. profile.sh $EXECUTABLE_NAME $OUTPUT_FILE_NAME`
Tracing the compiler generated futures only:
`. profile.sh $EXECUTABLE_NAME $OUTPUT_FILE_NAME --generated-future`
* After executing the script, we get a json file in the profile directory  
 ```
 profile
 ├── parser_nu.py
 ├── parser.py
 ├── profile.sh
 └── $OUTPUT_FILE_NAME.json
 ```  
 * Then we can use the trace-viewer to visualize the result:
   * Open the chrome browser
   * Type `chrome://tracing/` on your chrome browser
   * Load the json file generated by profiler
 * Result example:  
![image](https://user-images.githubusercontent.com/37073963/160839516-825f3e73-763b-4e73-84fe-e2ab433e6330.png)  

 ## TODO:
 * Different task(future) instances should be recognized
 * Combinators(e.g. `join!`, `select!`) issues
 * Speed up for parsing and recording are neeeded
 * Annotate different tasks with different colors
 * Tracing progress should be done correctly in release mode
 * Some locations information are wrong because of the same demangled symbol 
 ## License:
 * MIT license (http://opensource.org/licenses/MIT)
 
