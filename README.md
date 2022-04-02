# Rust-async-profiler
- Understand the behavior of your asynchronous tasks and futures.  
:warning: Only support the rust asynchronous programs that use `async-std` as runtime and use the futures generated by keyword `async`so far.(e.g. `async` funcitons and `async` blocks) 
## Prerequisite:
* Please install and build [uftrace](https://github.com/namhyung/uftrace) first
* Make sure using the **rust toolchain that supports `mcount` call** (the `mcount` flag is temporarily broken and see [here](https://github.com/namhyung/uftrace/issues/1392) for a workaround)  
and if the circumstances permit, you can just use the earlier toolchain (`nightly-2021-03-16-x86_64-unknown-linux-gnu`)
* Build your executable in **debug mode**  
e.g.(In `nightly-2021-03-16-x86_64-unknown-linux-gnu`)
```
RUSTFLAGS="-Z instrument-mcount" cargo build
```
## What is a profiling tool for asynchronous rust?
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
 ├── parser_nu.py (default)
 ├── parser.py (Not support yet)
 └── profile.sh
 ```
* Run the profiler script:  
`. profile.sh $EXECUTABLE_NAME $OUTPUT_FILE_NAME`
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
 * The data types that implement future trait should be recognized (I call them user-defined futures)
 * Different task(future) instances should be recognized
 * Combinators(e.g. `join!`, `select!`) issues
 * Speed up for parsing and recording are neeeded
 * Annotate different tasks with different colors
 ## License:
 * MIT license (http://opensource.org/licenses/MIT)
 
