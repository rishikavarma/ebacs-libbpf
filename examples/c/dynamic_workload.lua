local fio = require('fio')
local os = require('os')

-- Function to log distribution changes
local function log_change(phase, distribution)
    local f = io.open("fio_test.log", "a")
    f:write(string.format("[%s] Phase %s: Changed distribution to: %s\n", 
            os.date("%Y-%m-%d %H:%M:%S"), phase, distribution))
    f:close()
end

-- Function to create FIO config file
local function create_fio_config(distribution)
    local config = [[
[global]
ioengine=libaio
direct=0
bs=4k
size=4G
runtime=200
time_based=1
filename=testfile
rw=randrw
rwmixread=80
group_reporting=1

[hotspot]
random_distribution=]] .. distribution .. [[

numjobs=32
]]
    
    local f = io.open("fio_config.ini", "w")
    f:write(config)
    f:close()
end

-- Function to execute FIO with distribution changes
local function run_fio()
    local cmd = "fio fio_config.ini"
    local fio_process = io.popen(cmd)
    local start_time = os.time()
    local first_change_done = false
    
    -- Log initial phase
    log_change("1", "zoned:80/20:20/80")
    print("Phase 1: Started with distribution zoned:80/20:20/80")
    
    -- Monitor execution time
    while true do
        local current_time = os.time()
        local elapsed_time = current_time - start_time
        
        -- First change at 40 seconds
        if elapsed_time >= 40 and not first_change_done then
            os.execute("pkill fio")
            create_fio_config("zoned:50/50:50/50")
            fio_process = io.popen(cmd)
            first_change_done = true
            start_time = current_time  -- Reset timer for next change
            
            log_change("2", "zoned:50/50:50/50")
            print("Phase 2: Changed distribution to zoned:50/50:50/50")
        
        -- Second change at 80 seconds (40 seconds after first change)
        elseif elapsed_time >= 40 and first_change_done then
            os.execute("pkill fio")
            create_fio_config("zoned:80/20:20/80")
            fio_process = io.popen(cmd)
            
            log_change("3", "zoned:80/20:20/80")
            print("Phase 3: Returned to distribution zoned:80/20:20/80")
            break
        end
        
        os.execute("sleep 1")
    end
    
    -- Wait for final FIO execution to complete
    local output = fio_process:read("*a")
    fio_process:close()
    
    return output
end

-- Function to check if required programs are installed
local function check_requirements()
    local requirements = {
        {"fio", "FIO is not installed. Please install FIO first."},
        {"pkill", "pkill command not found. Please install procps package."}
    }
    
    for _, req in ipairs(requirements) do
        local cmd = string.format("which %s >/dev/null 2>&1", req[1])
        if os.execute(cmd) ~= 0 then
            print("Error: " .. req[2])
            os.exit(1)
        end
    end
end

-- Function to create results directory
local function setup_results_directory()
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local dir_name = string.format("fio_test_results_%s", timestamp)
    os.execute("mkdir -p " .. dir_name)
    return dir_name
end

-- Main execution function
local function main()
    -- Check requirements
    check_requirements()
    
    -- Create results directory
    local results_dir = setup_results_directory()
    print(string.format("Results will be stored in: %s", results_dir))
    
    -- Start with initial 80/20 distribution
    create_fio_config("zoned:80/20:20/80")
    
    -- Execute FIO with distribution changes
    print("\nStarting FIO test with dynamic distribution changes...")
    local result = run_fio()
    
    -- Save results
    local results_file = string.format("%s/fio_results.txt", results_dir)
    local f = io.open(results_file, "w")
    f:write(result)
    f:close()
    
    -- Move log file to results directory
    os.execute(string.format("mv fio_test.log %s/", results_dir))
    
    -- Cleanup temporary files
    os.remove("fio_config.ini")
    os.remove("testfile")
    
    print(string.format("\nTest completed. Results saved in %s", results_dir))
    print("\nFIO Test Results:")
    print(result)
end

-- Execute the test
main()