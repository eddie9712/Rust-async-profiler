import re
import subprocess
import io
import json
import sys

fp = open('dumped_data.txt',"r")

def output_in_json(process_name, threads_list, task_context_collection, output_name):
    trace_events = []
    for i in threads_list:
        name_of_label = "["+ i +"] " + process_name
        trace_events.append({"ts": 0, "ph":"M", "pid": i, "name": "process_name", "args":{ "name": name_of_label }})
        trace_events.append({"ts": 0, "ph":"M", "pid": i, "name": "thread_name", "args" : { "name": name_of_label }})
    for i in task_context_collection:    # Parse each events (28935.835212436  28875: [exit ] block_example::async_main::_{{closure}}(559bb1696e3e) depth: 37)
        if not re.search("::main::main::_{{closure}}\(", i):
            function_address = re.findall("\((.*)\)", i)[0]
            timestamp = re.findall("(.*)  ", i)
            if timestamp[0][0] == "T":
                timestamp[0] = timestamp[0].replace("T","")
            timestamp_m = float(timestamp[0]) * 1000000
            pid = threads_list[0]
            tid = re.findall("  (.*): \[", i)
            symbol_name = re.findall("\] (.*)\(", i)
            symbol_m = symbol_modification(symbol_name[0])
            location = find_location(i)
            status = re.findall("\[(.*)\]", i)
            if status[0] == 'entry':
                if tid[0] != pid:
                    trace_events.append({"ts": timestamp_m, "ph": "B", "pid": pid, "tid": tid[0], "name": symbol_m, "args": {"location": location}})
                else:    # Main thread
                    trace_events.append({"ts": timestamp_m, "ph": "B", "pid": pid, "name": symbol_m, "args": {"location": location}})
            else:
                if tid[0] != pid:
                    trace_events.append({"ts": timestamp_m, "ph": "E", "pid": pid, "tid": tid[0], "name": symbol_m, "args": {"location": location, "Function address (For recognizing anonymous type)": "0x"+function_address}})
                else:    # Main thread
                    trace_events.append({"ts": timestamp_m, "ph": "E", "pid": pid, "name": symbol_m, "args": {"location": location, "Function address (For recognizing anonymous type)": "0x"+function_address}})

    data = {"traceEvents": trace_events, "displayTimeUnit": "ms"} 
    jsonstring = json.dumps(data)
    jsonfile = open(output_name, "w")
    jsonfile.write(jsonstring)
    jsonfile.close()
def find_location(task_context):                       # find the location of the symbols
    symbol = re.findall("] (.*)\(",task_context)       # deal with the task_context
    symbol_m = re.sub("\.\.", "::", symbol[0])         # we need to modify the symbol generated from uftrace
    symbol_m = re.sub("_<", "<", symbol_m) 
    symbol_m = re.sub("_{", "{", symbol_m)
    output = subprocess.Popen('objdump -C --disassemble="'+ symbol_m +'" -l '+"../"+process_name +' | grep -e"<' + symbol_m + '>" -A 2', shell=True, stdout=subprocess.PIPE)  
    output_return = output.stdout.read().decode('utf-8')
    buf = io.StringIO(output_return)
    symbol_demangled = buf.readline()
    symbol = buf.readline()
    location = buf.readline().strip()
    return location
def symbol_modification(task_symbol):
    task_symbol = re.sub("::main::main","::main", task_symbol)
    if re.search(re.escape("async_std..task..join_handle..JoinHandle"), task_symbol):     # join_handle future
        return "join_handle_future"
    elif re.search("^async_std::", task_symbol):    # async_std future
        modified_symbol = re.findall("^(.*)::_{{closure}}", task_symbol)
        return modified_symbol[0]
    elif re.search("(.*)::_{{closure}}", task_symbol):    # compiler generated future
        modified_symbo = re.findall("(.*)::_{{closure}}", task_symbol)
        return modified_symbo[0]
    
task_context_collection = []        # To collect all polling contexts of tasks
In_task = ""                        # Record the task name to pair with task context
future_stack = []                   # Record the future name to pair
find_task_state = 0                 # Record the state of finding task context
polled_task_context_depth = 0
polled_future_context_depth = 0
last_state = 0                      # To record the last state for the seventh state 
thread_list = []
process_name = ""
output_name = ""

if sys.argv[1]:
    process_name = sys.argv[1]
if sys.argv[2]:
    output_name = sys.argv[2]+".json"
for line in fp:
    if re.search("reading (.*).dat", line): 
       threads = re.findall("reading (.*).dat", line)# record the threads that exist in the process
       thread_list.append(threads[0]) 
    if re.search("entry.*_<async_std..task..builder..SupportTaskLocals<F> as core..future..future..Future>::poll::_{{closure}}",line):
        find_task_state = 1
        get_task_depth = re.findall("depth: [0-9]*", line)
        get_task_depth_number = re.split('\s', get_task_depth[0])
        polled_task_context_depth = int(get_task_depth_number[1])+1     # The stack depth we expect for the poll function
        #print("0")
    if find_task_state == 1 and re.search("entry.*_<core..future..from_generator..GenFuture<T> as core..future..future..Future>::poll.*depth: "+str(polled_task_context_depth), line):
        find_task_state = 2
        #print("1")
    if find_task_state == 1 and re.search("entry] _<.* as core..future..future..Future>::poll\(", line): # task context (join_handle case)
        if not re.search("entry.*_<core..future..from_generator.GenFuture<T> as core..future..future..Future>::poll\(", line):
            task_context_collection.append(line)
            get_future_name = re.findall("entry] (.*)\(", line)
            future_stack.append(str(get_future_name[0]))
            find_task_state = 7
            last_state = 1
    #if find_task_state == 1 and re.search("as core..future..future..Future>::poll\(", line)     # Get user-defined future
    #    task_context_collection.append(line)
    #    get_future_name = re.findall("entry] (<.*>)", line)
    #    future_stack.append(str(get_future_name[0]))
    #    find_task_state = 7
    #    last_state = 1
    if find_task_state == 2 and re.search("entry.*::_{{closure}}.*depth: "+str(polled_task_context_depth+1), line):    # Get into the task context
        task_context_collection.append(line)
        get_task_name = re.findall("entry] (.*::_{{closure}})", line)    # Get the symbol of the task
        find_task_state = 3
        In_task = str(get_task_name[0])    # When in the task state, it may encounter the inner futures or exit the task
        #print("2")
    if find_task_state == 3 and re.search(re.escape("exit ] "+In_task+"("), line):    #if there is no inner futures inside the task
        task_context_collection.append("T"+line)
        find_task_state = 0
        #print("3")
    elif find_task_state == 3 and re.search("entry.*_<core..future..from_generator..GenFuture<T> as core..future..future..Future>::poll.*depth: ", line):    # if there are inner futures
        get_future_depth = re.findall("depth: [0-9]*",line)        # save the depth of polling function
        get_future_depth_number = re.split('\s', get_future_depth[0])
        polled_future_context_depth = int(get_future_depth_number[1])+1
        find_task_state = 4
        #print("3")
    if find_task_state == 3 and re.search("entry] _<.* as core..future..future..Future>::poll\(", line):
        if not re.search("entry.*_<core..future..from_generator.GenFuture<T> as core..future..future..Future>::poll\(", line):
            task_context_collection.append(line)
            get_future_name = re.findall("entry] (.*)\(", line)
            future_stack.append(str(get_future_name[0]))
            find_task_state = 7
            last_state = 3
            #print("3")
    if find_task_state == 4 and re.search("entry.*::_{{closure}}.*depth: "+str(polled_future_context_depth), line):    #find future polling
        #print(line)
        task_context_collection.append(line)
        get_future_name = re.findall("entry] (.*::_{{closure}})", line)
        future_stack.append(str(get_future_name[0]))
        find_task_state = 5
        #print("4")
    if find_task_state == 5 and future_stack and re.search(re.escape("exit ] "+future_stack[-1]+"("), line):    #find exit of future
        future_stack.pop()
        task_context_collection.append(line)
        find_task_state = 6
        #print("5")
    elif find_task_state == 5 and re.search("entry.*_<core..future..from_generator..GenFuture<T> as core..future..future..Future>::poll.*depth: ", line):    # find inner future
        get_future_depth = re.findall("depth: [0-9]*", line)
        get_future_depth_number = re.split('\s', get_future_depth[0])
        polled_future_context_depth = int(get_future_depth_number[1])+1
        find_task_state = 4
        #print("5")
    if find_task_state == 5 and re.search("entry] _<.* as core..future..future..Future>::poll\(", line):
        if not re.search("entry.*_<core..future..from_generator.GenFuture<T> as core..future..future..Future>::poll\(", line):
            task_context_collection.append(line)
            get_future_name = re.findall("entry] (.*)\(", line)
            future_stack.append(str(get_future_name[0]))
            find_task_state = 7
            last_state = 5
        #print("5")
    if find_task_state == 7 and re.search(re.escape("exit ] "+future_stack[-1]+"("), line):
        task_context_collection.append(line)
        future_stack.pop()
        if last_state == 3:
            find_task_state = 3
        elif last_state == 5:
            find_task_state = 5
        elif last_state == 1:
            find_task_state = 0
            task_context_collection[-1] = "T"+line
        elif last_state == 6:
            find_task_state = 6
        #print("7")
    if find_task_state == 6 and re.search("entry.*_<core..future..from_generator..GenFuture<T> as core..future..future..Future>::poll.*depth: ", line):
        get_future_depth = re.findall("depth: [0-9]*", line)
        get_future_depth_number = re.split('\s', get_future_depth[0])
        polled_future_context_depth = int(get_future_depth_number[1])+1
        find_task_state = 4
        #print("6") 
    elif find_task_state == 6 and future_stack and re.search(re.escape("exit ] "+future_stack[-1]+"("), line):
        future_stack.pop()
        task_context_collection.append(line)
        #print("6")
    elif find_task_state == 6 and re.search(re.escape("exit ] "+In_task+"("), line):
        task_context_collection.append("T"+line)
        find_task_state = 0
        #print("6")
    if find_task_state == 6 and re.search("entry] _<.* as core..future..future..Future>::poll\(", line):    #find join_handle_future
        if not re.search("entry.*_<core..future..from_generator.GenFuture<T> as core..future..future..Future>::poll\(", line):
            task_context_collection.append(line)
            #print(line)
            get_future_name = re.findall("entry] (.*)\(", line)
            future_stack.append(str(get_future_name[0]))
            last_state = 6
            find_task_state = 7 
for i in task_context_collection:
    #print(i+"\n")
    print(i + "location:" + find_location(i) + "\n")
#output_in_json(process_name, thread_list, task_context_collection, output_name)
#print(thread_list)