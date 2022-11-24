# I used this script to parse the logfiles 
# Many things are hardcoded but can be easily adapted for any tracing outputs which are either numerical or log 2 histograms
import gzip
import pandas
import re
import os

re_mmtkstats = re.compile("============================ MMTk Statistics Totals ============================")
re_digit = re.compile("\d+")

# Processes all files at the given location 
def parse_all(logpath):
    for f in os.scandir(logpath):
        if f.is_file() and ".gz" in f.name:
            d = f.name
            # figure out filename
            fname = d.split('.')[0]
            nthreads = d.partition("gc_threads-")[2].split('.')[0]
            fname = fname + "_" + nthreads
            #if "after" in d:
                #fname = fname + "_after"
            #elif "before" in d:
                #fname = fname + "_before"
            # scale(logpath+"/"+d,fname)
            # objcount(logpath+"/"+d,fname)
            processedges(logpath+"/"+d, fname)


# processes data for ProcessEdges packet size / root packet size distribution experiment
def processedges(logpath, filename):
    f = gzip.open(logpath, 'rt')
      
    results = {}
    roots = {}
    pe = {}
    inv_count = 0
    n = 0
    ids = False
    skip = False
    pedge = False
    root = False
    threadcount = 0 
    hist = ""
    total = False
    store = {}
    
    f1 = gzip.open(logpath, 'rt')
    
    for l in f1:
        # start of a new invocation
        if re_mmtkstats.match(l):
            skip = False
        
        # skip until the invocation finishes
        elif "starting warmup 1 =====" in l:
            skip = True
            inv_count = inv_count + 1
            threadcount = 0
            pe[inv_count] = {}
            results[inv_count] = {}
            
        # unfinished invocations 
        elif skip:
            continue
        
        # end of bpf tracing
        elif ids and "^C" in l:
            ids = False
          
        # get process edges total work 
        elif "@processedgeswork" in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            # add to results
            y = re.findall(r'\d+', l)
            t = store[y[0]]
            results[inv_count][t][1000000000] = x[0]

        # start of process edges histogram
        elif "@processedgeslen" in l:
            total = True
            
        elif total and l in ['\n', '\r\n']:
            total = False
            
        elif total:
            x = re.findall(r'\d+', l)
            if "[0]" in l:
                pe[inv_count][0] = int(x[1])
            elif "[1]" in l:
                pe[inv_count][1] = int(x[1])
            elif int(x[0]) == 512:
                pe[inv_count][int(x[0])] = int(x[2])
            elif "K" in l:
                pe[inv_count][pow(2,10) * int(x[0])] = int(x[2])
            else:
                pe[inv_count][int(x[0])] = int(x[2])
            
        # start of process edges histogram by thread
        elif "@packetsize" in l:
             pedge = True
             threadcount = threadcount + 1
             if threadcount not in results[inv_count].keys():
                 results[inv_count][threadcount] = {}
             hist = threadcount
             x = re.findall(r'\d+', l)
             store[x[0]] = threadcount
             results[inv_count][threadcount][1000000000] = {}
            
        # end of histogram
        elif pedge and l in ['\n', '\r\n']:
            pedge = False
            hist = ""
            
        # save data to histogram 
        elif pedge:
            x = re.findall(r'\d+', l)
            if "[0]" in l:
                results[inv_count][hist][0] = int(x[1])
            elif "[1]" in l:
                results[inv_count][hist][1] = int(x[1])
            elif int(x[0]) == 512 and "512K" not in l:
                results[inv_count][hist][int(x[0])] = int(x[2])
            elif "K" in l:
                results[inv_count][hist][pow(2,10) * int(x[0])] = int(x[2])
            else:
                results[inv_count][hist][int(x[0])] = int(x[2])
                
        # start of root edges histogram
        elif "@roots" in l:
            root = True
            roots[inv_count] = {}
        
        # end of histogram
        elif root and l in ['\n', '\r\n']:
            root = False
            
        # save data to histogram
        elif root: 
        # elif hist != "" and pedge:
            x = re.findall(r'\d+', l)
            if "[0]" in l:
                roots[inv_count][0] = int(x[1])
            elif "[1]" in l:
                roots[inv_count][1] = int(x[1])
            elif int(x[0]) == 512:
                roots[inv_count][int(x[0])] = int(x[2])
            elif "K" in l:
                roots[inv_count][pow(2,10) * int(x[0])] = int(x[2])
            else:
                roots[inv_count][int(x[0])] = int(x[2])
        n = n + 1
    f.close()
    
    # convert results to pandas, sort, compute mean and output to excel

    r = pandas.DataFrame.from_dict(roots, orient='columns').fillna(0)
    r.sort_index(ascending=True)
    r['mean'] = r.mean(axis=1)
    
    p = pandas.DataFrame.from_dict(pe, orient='columns').fillna(0)
    p.sort_index(ascending=True)
    p['mean'] = p.mean(axis=1)
    
    with pandas.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter') as writer:
        counter = 1
        r.to_excel(writer, sheet_name='hist', startrow=counter, startcol=0)
        counter = counter + len(r) + 3
        p.to_excel(writer, sheet_name='hist', startrow=counter, startcol=0)
        counter = counter + len(p) + 3
        for i in results.keys():
            temp = pandas.DataFrame.from_dict(results[i], orient='columns').fillna(0)
            temp.sort_index(ascending=True)
            temp.to_excel(writer, sheet_name='hist', startrow=counter, startcol=0)
            counter = counter + len(temp) + 3

# processes data for work packet type experiment & is an old version for process edges experiments
# a_name is for cumulative time by work packet, c_name is for work packet counters, type_name is for type names
# b_name is for process edges packet size distribution, root_name is for root packet size distribution
def typeid(logpath, filename, a_name,b_name, c_name,h_name,root_name,type_name):
    f = gzip.open(logpath, 'rt')
    time = {}
    results = {}
    types = {}
    acc = {}
    inv_count = 0
    inv_start = -100
    n = 0
    ids = False
    # hist = ""
    skip = False

    for l in f:
        # skip until the invocation finishes
        if "starting warmup 1 =====" in l:
            inv_count = inv_count + 1
            types[inv_count] = {}
            
        # start of types
        elif "@{}".format(type_name) in l:
            x = re.findall(r'\d+', l)
            typename = ""
            m = 1
            record = False
            while m >= 1:
                if m >= len(l) or l[m] == '<':
                    break
                if l[m].isupper():
                    record = True
                if record:
                    typename = typename + str(l[m])
                m = m + 1 
            types[inv_count][x[0]] = typename
            
    results = {}
    roots = {}
    acc = {}
    count = {}
    inv_count = 0
    inv_start = -100
    n = 0
    ids = False
    # hist = ""
    skip = False
    pedge = False
    root = False
    
    f1 = gzip.open(logpath, 'rt')
    
    for l in f1:
        # start of a new invocation
        if re_mmtkstats.match(l):
            skip = False
            inv_start = n
        
        # skip until the invocation finishes
        elif "starting warmup 1 =====" in l:
            skip = True
            inv_count = inv_count + 1
            time[inv_count] = {}
            acc[inv_count] = {}
            count[inv_count] = {}
            results[inv_count] = {}
            acc[inv_count]["sum"] = 0
            roots[inv_count] = {}
            
        # unfinished invocations 
        elif skip:
            continue

        # get time.stw 
        elif n == inv_start + 2:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            acc[inv_count]["time.stw"] = x[2] * 1000000
        
        # end of bpf tracing
        elif ids and "^C" in l:
            ids = False
            
        # get acc
        elif "@{}".format(a_name) in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            y = re.findall(r'\d+', l)
            c = types[inv_count][y[0]] + str(y[0])
            # add to results
            acc[inv_count][c] = x[0]
            acc[inv_count]["sum"] = acc[inv_count]["sum"] + x[0]
            
        # get counter
        elif "@{}".format(c_name) in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            y = re.findall(r'\d+', l)
            c = types[inv_count][y[0]] + str(y[0])
            # add to results
            count[inv_count][c] = x[0]
            
        # get process edges time
        elif "@{}".format(b_name) in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            # add to results
            acc[inv_count]["time.processedges"] = x[0]

        # start of process edges histogram
        elif "@{}".format(h_name) in l:
            # hist = "process_edges_packet_size"
            # results[inv_count][hist] = {}
            pedge = True
        
        # end of histogram
        elif pedge and l in ['\n', '\r\n']:
            pedge = False
            
        # save data to histogram
        elif pedge: 
        # elif hist != "" and pedge:
            x = re.findall(r'\d+', l)
            if "[0]" in l:
                results[inv_count][0] = int(x[1])
            elif "[1]" in l:
                results[inv_count][1] = int(x[1])
            elif int(x[0]) == 512 and "512K" not in l:
                results[inv_count][int(x[0])] = int(x[2])
            elif "K" in l:
                results[inv_count][pow(2,10) * int(x[0])] = int(x[2])
            else:
                results[inv_count][int(x[0])] = int(x[2])
                
        
        # start of root edges histogram
        elif "@{}".format(root_name) in l:
            # hist = "process_edges_packet_size"
            # results[inv_count][hist] = {}
            root = True
        
        # end of histogram
        elif root and l in ['\n', '\r\n']:
            root = False
            
        # save data to histogram
        elif root: 
        # elif hist != "" and pedge:
            x = re.findall(r'\d+', l)
            if "[0]" in l:
                roots[inv_count][0] = int(x[1])
            elif "[1]" in l:
                roots[inv_count][1] = int(x[1])
            elif int(x[0]) == 512:
                roots[inv_count][int(x[0])] = int(x[2])
            elif "K" in l:
                roots[inv_count][pow(2,10) * int(x[0])] = int(x[2])
            else:
                roots[inv_count][int(x[0])] = int(x[2])

        # start of work packets histogram
        # elif "@{}".format(hist_name) in l:
            # pedge = False
            # x = re.findall(r'\d+', l)
            # hist = types[inv_count][x[0]] + str(x[0])
            # results[inv_count][hist] = {}
        
        # end of histogram
        # elif hist != "" and l in ['\n', '\r\n']:
            # hist = ""
            
        # save data to histogram
        # elif hist != "":
            # x = re.findall(r'\d+', l)
            # if "[0]" in l or "[1]" in l:
                # results[inv_count][hist][x[0]] = x[1] 
            # else:
                # results[inv_count][hist][x[0]] = x[2]
        n = n + 1
    f.close()
    
    #a = pandas.DataFrame.from_dict(acc, orient='columns').fillna(0)
    #a['mean'] = a.mean(axis=1)
    
    #ct = pandas.DataFrame.from_dict(count, orient='columns').fillna(0)
    #ct['mean'] = ct.mean(axis=1)
    
    #tid = pandas.DataFrame.from_dict(types, orient='columns').fillna(0)
    
    dist = pandas.DataFrame.from_dict(results, orient='columns').fillna(0)
    dist.sort_index(ascending=True)
    # dist['mean'] = dist.mean(axis=1)
    
    #rootsdist = pandas.DataFrame.from_dict(roots, orient='columns').fillna(0)
    #rootsdist.sort_index(ascending=True)
    #rootsdist['mean'] = rootsdist.mean(axis=1)
    
    with pandas.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter') as writer:
        counter = 1
        #a.to_excel(writer, sheet_name='time', startrow=counter, startcol=0)
        #ct.to_excel(writer, sheet_name='counter', startrow=counter, startcol=0)
        # tid.to_excel(writer, sheet_name='id', startrow=counter, startcol=0)
        dist.to_excel(writer, sheet_name='distribution', startrow=counter, startcol=0)
        #counter = counter + len(dist) + 3
        # rootsdist.to_excel(writer, sheet_name='distribution', startrow=counter, startcol=0)
        # i = 1
        # while i < len(results) + 1:
            #temp = pandas.DataFrame.from_dict(results[i], orient='columns').fillna(0)
            #temp.to_excel(writer, sheet_name='hist', startrow=counter, startcol=0)
            #counter = counter + len(temp) + 3
            #i = i + 1

# processes data for scalability measurement of ProcessEdges
def scale(logpath, filename):
    f = gzip.open(logpath, 'rt')

    acc = {}
    inv_count = 0
    inv_start = -100
    n = 0
    ids = False
    skip = False
    
    for l in f:
        # start of a new invocation
        if re_mmtkstats.match(l):
            skip = False
            inv_start = n
        
        # skip until the invocation finishes
        elif "starting warmup 1 =====" in l:
            skip = True
            inv_count = inv_count + 1
            acc[inv_count] = {}
            
        # unfinished invocations 
        elif skip:
            continue

        # get time.stw 
        elif n == inv_start + 2:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            acc[inv_count]["time.stw"] = x[2] * 1000000
        
        # end of bpf tracing
        elif ids and "^C" in l:
            ids = False
            
        # get pe time
        elif "@processedgessum" in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            # add to results
            acc[inv_count]["time.processedges"] = x[0]
         
        n = n + 1
    f.close()
    
    a = pandas.DataFrame.from_dict(acc, orient='columns').fillna(0)
    a['mean'] = a.mean(axis=1)
    
    with pandas.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter') as writer:
        counter = 1
        a.to_excel(writer, sheet_name='time', startrow=counter, startcol=0)
        
# processes data for distribution of number of outgoing edges for objects 
def objcount(logpath, filename):
    f = gzip.open(logpath, 'rt')

    acc = {}
    inv_count = 0
    inv_start = -100
    n = 0
    ids = False
    skip = True
    
    for l in f:
        # start of a new invocation
        if re_mmtkstats.match(l):
            skip = False
            inv_start = n
        
        # skip until the invocation finishes
        elif "starting warmup 1 =====" in l:
            skip = True
            inv_count = inv_count + 1
            acc[inv_count] = {}
            
        # unfinished invocations 
        elif skip:
            continue

        # get time.stw 
        elif n == inv_start + 2:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            acc[inv_count]["time.stw"] = x[2] * 1000000
        
        # end of bpf tracing
        elif ids and "^C" in l:
            ids = False
            
        # get edge count
        elif "@edgecount" in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            # add to results
            acc[inv_count]["edgecount"] = x[0]
            
        # get object count
        elif "@objcount" in l:
            x = []
            for t in l.split():
                try:
                    x.append(float(t))
                except ValueError:
                    pass
            # add to results
            acc[inv_count]["objcount"] = x[0]
         
        n = n + 1
    f.close()
    
    a = pandas.DataFrame.from_dict(acc, orient='columns').fillna(0)
    a['mean'] = a.mean(axis=1)
    
    with pandas.ExcelWriter('{}.xlsx'.format(filename), engine='xlsxwriter') as writer:
        counter = 1
        a.to_excel(writer, sheet_name='time', startrow=counter, startcol=0)