from datetime import datetime, timedelta
from tabulate import tabulate
import argparse
import random
import string

def rand_string(length):
    letters = string.ascii_letters
    digits = string.digits
    return ''.join(random.choice(letters + digits) for i in range(length))

class Task:
    def __init__(self, tid, dtsoft, dthard, name, priority, completion, delayed=0):
        self.id = tid
        self.dtsoft = dtsoft
        self.dthard = dthard
        self.name = name
        self.priority = priority
        self.completion = completion # 0: current task; 1: completed; 2: cancelled
        self.delayed = delayed

    def __lt__(self, self2): # more important: greater value
        if self.completion != self2.completion:
            return self.completion > self2.completion
        
        statsa = self.status() if self.status() else 1
        statsb = self2.status() if self2.status() else 1
        #print(self.name, self2.name, statsa, statsb)
        
        if statsa != statsb:
            return statsa < statsb
        
        if self.priority != self2.priority:
            return self.priority < self2.priority
        if self.dtsoft > self2.dtsoft and self.dthard > self2.dthard:
            return True
        if self.dtsoft < self2.dtsoft and self.dthard < self2.dthard:
            return False
        return self.dtsoft > self2.dtsoft
    
    def __gt__(self, self2):
        return not self < self2
    
    def __str__(self):
        return f"{self.id} {self.name} {self.priority}\nSoft {datetime.strftime(self.dtsoft, "%y-%m-%d %H:%M")}\nHard {datetime.strftime(self.dthard, "%y-%m-%d %H:%M")}\n{"Completed" if self.completion == 1 else "Not Completed" if self.completion == 0 else "Cancelled"}"

    def extend(self, diff, mode, skipadd=False):
        """
        0: soft only
        1: hard only
        2: both
        """
        if not mode%2: self.dtsoft += diff
        if mode: self.dthard += diff
        if not skipadd: self.delayed += 1

    def prioritise(self, delta):
        self.priority += delta
        
    def status(self):
        if self.completion == 2:
            return -2 #"Cancelled"
        if self.completion == 1:
            return -1 #"Completed"
        softdiff = self.dtsoft - datetime.now()
        harddiff = self.dthard - datetime.now()
        if harddiff.days < 0:
            return 3 #"Overdue"
        if softdiff.days < 0:
            return 2 #"Danger"
        if softdiff.days < 3:
            return 1 #"Soon"
        return 0

def weekdaytostring(dow):
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return weekday[dow]

def weekdaytonum(wod):
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return weekday.index(wod)

def outputdt(dtevent):
    diff = dtevent - datetime.now()
    
    diffdays = diff.days if dtevent.hour > datetime.now().hour else diff.days + 1
    
    hourminu = datetime.strftime(dtevent, "%H:%M")
    
    if hourminu == "00:00":
        hourminu = ""
    
    if diffdays < -1:
        return str(-diff.days) + "d ago"
    if diffdays < 0:
        return "Yesterday " + hourminu
    if diffdays == 0 and dtevent.day == datetime.now().day:
        return "Today " + hourminu
    if diffdays == (0 or 1) and dtevent.day == (datetime.now()+timedelta(1)).day:
        return "Tomorrow " + hourminu
    if diffdays < 7 and dtevent.weekday() > datetime.now().weekday():
        return weekdaytostring(dtevent.weekday())
    if diffdays < 7 and dtevent.weekday() <= datetime.now().weekday():
        return "Next " + weekdaytostring(dtevent.weekday()) 
    if diffdays < 10:
        return "In " + str(diff.days) + "d"
    #return datetime.strftime(dtevent, "%Y-%m-%d %H:%M")
    return datetime.strftime(dtevent, "%Y-%m-%d")

def showtasks(TaskList, withcomplete=False, withcancel=False):
    print("\n\n" + datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") + ", " + weekdaytostring(datetime.now().weekday()))
    
    if withcomplete and withcancel:
        print("All Tasks:")
    elif withcomplete:
        print("Current and Completed Tasks:")
    elif withcancel:
        print("Current and Cancelled Tasks:")
    else:
        print("Current Tasks:")
        
    outputlist = [["ID", "Name", "Soft Deadline", "Hard Deadline", "Priority"]]
    
    TaskList = sorted(TaskList, reverse=True)
    
    for task in TaskList:
        
        softdiff = task.dtsoft - datetime.now()
        harddiff = task.dthard - datetime.now()
        
        if not withcomplete and task.completion == 1:
            continue
        if not withcancel and task.completion == 2:
            continue
        
        if task.completion == 2:
            outputlist.append(["\033[37m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif task.completion == 1:
            outputlist.append(["\033[32m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif softdiff.days < 0 and harddiff.days >= 0: # red
            outputlist.append(["\033[91m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif harddiff.days < 0: # red & bold & underline
            outputlist.append(["\033[1m\033[91;103m\033[4m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m\033[0m\033[0m"])
        
        elif softdiff.days < 3 or task.delayed >= 2: # yellow
            outputlist.append(["\033[93m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif task.delayed: # ok blue
            outputlist.append(["\033[96m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        else: # ok green
            outputlist.append(["\033[92m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
    print(tabulate(outputlist))
    
    a = int(input("\n\n1. " + ("Hide" if withcomplete else "Show") + " Completed\n2. " + ("Hide" if withcancel else "Show") + " Cancelled\n3. Add Task\n4. Modify Task\n5. Save & Quit\n6. Force Quit\n%> ") or 0)
    return a

def addtask(TaskList, TaskDict):
    name = input("Enter Task Name: ")
    priority = int(input("Enter Task Priority [10]: ") or 10)
    
    a = input("Allowed formats: 241231; 241231T2359; Mon-Sun\nEnter Hard Deadline: ")
    
    try:
        dthard = datetime.strptime(a, "%y%m%dT%H%M")
    except ValueError:
        try:
            dthard = datetime.strptime(a, "%y%m%d")
        except ValueError:
            try:
                wday = weekdaytonum(a)
            except ValueError:
                print("Unable to identify datetime. Quitting...")
                return TaskList, TaskDict
            dtnow = datetime.now()
            if wday >= dtnow.weekday():
                dthard = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday - dtnow.weekday())
            else:
                inpast = input("Add task that's due in the past? (Y/N): ").strip().lower()
                if inpast == "y":
                    dthard = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday - dtnow.weekday())
                else:
                    dthard = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday + 7 - dtnow.weekday())
    
    b = input("\nAllowed formats: 241231; 241231T2359; Mon-Sun\nEnter Soft Deadline [3 days before Hard]: ")
    
    if not b:
        dtsoft = dthard + timedelta(days=-3)
        
    else:
        try:
            dtsoft = datetime.strptime(b, "%y%m%dT%H%M")
        except ValueError:
            try:
                dtsoft = datetime.strptime(b, "%y%m%d")
            except ValueError:
                try:
                    wday = weekdaytonum(b)
                except ValueError:
                    print("Unable to identify datetime. Quitting...")
                    return TaskList, TaskDict
                dtnow = datetime.now()
                if wday >= dtnow.weekday():
                    dtsoft = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday - dtnow.weekday())
                else:
                    inpast = input("Add task that's due in the past? (Y/N): ").strip().lower()
                    if inpast == "y":
                        dtsoft = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday - dtnow.weekday())
                    else:
                        dtsoft = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday + 7 - dtnow.weekday())
    
    if dtsoft > dthard:
        print("Error: Soft deadline cannot happen after hard deadline. \nSetting to 3 days before hard deadline...")
        dtsoft = dthard + timedelta(days=-3)
    
    tid = rand_string(3).lower()
    while tid in TaskDict.keys():
        tid = rand_string(3).lower()
    
    NewTask = Task(tid, dtsoft, dthard, name, priority, False, 0)
    
    res = input("\n\n" + str(NewTask) + "\n\nConfirm Task Creation? (Y/N): ")[0].lower() == "y"
    
    if res:
        TaskList.append(NewTask)
        TaskDict[tid] = (NewTask, len(TaskList)-1) # store index
    else:
        print("New Task Abandoned")
    
    return TaskList, TaskDict

def writetofile(TaskList, file):
    with open(file, "w+", encoding="UTF-8") as g:
        for task in TaskList:
            g.write(task.id + " " +
                    datetime.strftime(task.dtsoft, "%y%m%dT%H%M") + " " +
                    datetime.strftime(task.dthard, "%y%m%dT%H%M") + " " +
                    task.name.replace(" ", "_") + " " + str(task.priority) + " " +
                    str(task.delayed) + "\n")
    return

def modifytask(TaskList, TaskDict, tid):
    keyset = set(TaskDict.keys())
    tid = tid.strip().lower()
    if not tid in keyset:
        print("\nTID not found. Reloading")
        return TaskList, TaskDict
    task, listindex = TaskDict[tid]
    if TaskList[listindex] != task:
        print("\nUnknown Error. Quitting")
        return TaskList, TaskDict
    #print(task.id, task.dtsoft, task.dthard, task.name, task.priority, task.completed, task.delayed)

    a = int(input("\n" + str(task) + "\n1. Toggle completion\n2. Change name\n3. Change priority\n4. Delay task\n5. Toggle cancellation\n6. Return\n%> ") or 6)
    
    if a == 6:
        return TaskList, TaskDict
    
    if a == 1:
        if task.completion == 2:
            print("Error: Cannot complete a cancelled task")
            return TaskList, TaskDict
        elif task.completion == 0:
            tidext = rand_string(3).lower()
            while task.id + tidext in keyset:
                tidext = rand_string(3).lower()
            task.id += tidext
            print(tidext, task.id)
            task.completion = 1
        elif task.completion == 1:
            tidtemp = task.id[0:3]
            while tidtemp in keyset:
                tidtemp = rand_string(3).lower()
            task.id = tidtemp
            task.completion = 0
        
    if a == 5:
        if task.completion == 1:
            print("Error: Cannot cancel a completed task")
            return TaskList, TaskDict
        elif task.completion == 0:
            tidext = rand_string(2).lower()
            while task.id + tidext in keyset:
                tidext = rand_string(2).lower()
            task.id += tidext
            task.completion = 2
        elif task.completion == 2:
            tidtemp = task.id[0:3]
            while tidtemp in keyset:
                tidtemp = rand_string(3).lower()
            task.id = tidtemp
            task.completion = 0
    
    if a == 2:
        task.name = input("Enter New Name: ") or task.name
    if a == 3:
        task.prioritise(int(input("Enter New Priority: ") or task.priority) - task.priority)
    if a == 4:
        b = int(input("Delay days [0]: ") or 0)
        c = 3600 * int(input("Delay hours [0]: ") or 0)
        c += 60 * int(input("Delay mins [0]: ") or 0)
        c += int(input("Delay seconds [0]: ") or 0)
        mode = int(input("Delay [1]Soft [2]Hard [3]Both: ") or 3)
        #skipadd = bool(int(input("Not add to count?") or 0))
        task.extend(timedelta(days=b, seconds=c), mode-1, skipadd=False)
    
    TaskList[listindex] = task
    TaskDict.pop(tid)
    TaskDict[task.id] = (task, listindex)
    return TaskList, TaskDict

parser = argparse.ArgumentParser(description="""
                                 Hello.
                                 """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-r", "--read", help="read from file")
parser.add_argument("-w", "--write", help="write to file")
args = parser.parse_args()
config = vars(args)

read = str(config['read']) if config['read'] else None
write = str(config['write']) if config['write'] else None 

TaskList = []
TaskDict = {}

if not (read and write):
    raise ValueError

with open(read, "r+", encoding="UTF-8") as f:
    item = f.readline()
    while item:
        item = item.strip()
        objects = item.split()
        if not objects:
            break
        tid = objects[0]
        
        completion = 0 if len(tid) == 3 else 1 if len(tid) == 6 else 2
        # length 3 -> completion 0, current task
        # length 6 -> completion 1, completed
        # length 5 -> completion 2, cancelled
        
        dtsoft = datetime.strptime(objects[1], "%y%m%dT%H%M")
        dthard = datetime.strptime(objects[2], "%y%m%dT%H%M")
        name = objects[3].replace("_", " ")
        priority = int(objects[4])
        #completed = bool(objects[5] == "True")
        delayed = int(objects[5]) # times that it has been delayed

        NewTask = Task(tid, dtsoft, dthard, name, priority, completion, delayed)
    
        if tid in TaskDict.keys():
            print(f"Error loading task:\n{tid} {name}\nTID exists, skipping...")

        TaskList.append(NewTask)
        TaskDict[tid] = (NewTask, len(TaskList)-1) # store index

        item = f.readline()

withcomplete = False
withcancel = False

while True:
    option = showtasks(TaskList, withcomplete, withcancel)
    #print(option)
    #if option == 0:
    if option == 1:
        withcomplete = not withcomplete
    if option == 2:
        withcancel = not withcancel
    if option == 3:
        TaskList, TaskDict = addtask(TaskList, TaskDict)
    if option == 4:
        TaskList, TaskDict = modifytask(TaskList, TaskDict, input("Enter tid: "))
    if option == 5:
        writetofile(TaskList, write)
        break
    if option == 6:
        a = input("Confirm? (Y/N): ").strip().lower()
        if a == "y":
            break
