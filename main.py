from datetime import datetime, timedelta
from configparser import ConfigParser
from tabulate import tabulate
import argparse
import random
import string

def rand_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

class Task:
    def __init__(self, tid, dtsoft, dthard, name, priority, completed, delayed=0):
        self.id = tid
        self.dtsoft = dtsoft
        self.dthard = dthard
        self.name = name
        self.priority = priority
        self.completed = completed
        self.delayed = delayed

    def __lt__(self, self2): # more important: greater value
        if self.completed and not self2.completed:
            return True
        if not self.completed and self2.completed:
            return False
        
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
        return f"{self.id} {self.name} {self.priority}\nSoft {datetime.strftime(self.dtsoft, "%y-%m-%d %H:%M")}\nHard {datetime.strftime(self.dthard, "%y-%m-%d %H:%M")}\n{"Completed" if self.completed else "Not Completed"}"

    def togcomplete(self):
        self.completed = not self.completed

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
        if self.completed:
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
    if diff.days < -1:
        return str(-diff.days) + "d ago"
    if diff.days < 0:
        return "Yesterday"
    if diff.days == 0 and dtevent.day == datetime.now().day:
        return "Today"
    if diff.days == (0 or 1) and dtevent.day == (datetime.now()+timedelta(1)).day:
        return "Tomorrow"
    if diff.days < 7 and dtevent.weekday() > datetime.now().weekday():
        return weekdaytostring(dtevent.weekday()) 
    if diff.days < 7 and dtevent.weekday() <= datetime.now().weekday():
        return "Next " + weekdaytostring(dtevent.weekday()) 
    if diff.days < 10:
        return "In " + str(diff.days) + "d"
    return datetime.strftime(dtevent, "%Y-%m-%d %H:%M")

def showtasks(TaskList, withcomplete=False):
    print("\n\n" + datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M") + ", " + weekdaytostring(datetime.now().weekday()))
    print("Current Tasks:" if not withcomplete else "All Tasks:")
    outputlist = [["ID", "Name", "Soft Deadline", "Hard Deadline", "Priority"]]
    
    TaskList = sorted(TaskList, reverse=True)
    
    for task in TaskList:
        
        softdiff = task.dtsoft - datetime.now()
        harddiff = task.dthard - datetime.now()
        
        if not withcomplete and task.completed:
            continue
        
        if softdiff.days < 0 and harddiff.days >= 0: # red
            outputlist.append(["\033[91m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif harddiff.days < 0: # red & bold & underline
            outputlist.append(["\033[1m\033[91m\033[4m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m\033[0m\033[0m"])
        
        elif softdiff.days < 3 or task.delayed >= 2: # yellow
            outputlist.append(["\033[93m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        elif task.delayed: # ok cyan
            outputlist.append(["\033[96m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
        else: # ok green
            outputlist.append(["\033[92m" + task.id, task.name, outputdt(task.dtsoft), outputdt(task.dthard), str(task.priority) + "\033[0m"])
        
    print(tabulate(outputlist))
    
    a = int(input("\n\n1. " + ("Hide" if withcomplete else "Show") + " Completed\n2. Add Task\n3. Modify Task\n4. Save\n5. Quit\n%> ") or 0)
    return a

def addtask(TaskList, TaskDict):
    name = input("Enter Task Name: ")
    priority = int(input("Enter Task Priority: [10]") or 10)
    
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
                inpast = input("Add task that's due in the past? (T/F): ")
                if inpast == "T":
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
                    inpast = input("Add task that's due in the past? (T/F): ")
                    if inpast == "T":
                        dtsoft = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday - dtnow.weekday())
                    else:
                        dtsoft = datetime(dtnow.year, dtnow.month, dtnow.day) + timedelta(days = wday + 7 - dtnow.weekday())
    
    if dtsoft > dthard:
        print("Error: Soft deadline cannot happen after hard deadline. \nSetting to 3 days before hard deadline...")
        dtsoft = dthard + timedelta(days=-3)
    
    tid = rand_string(6).lower()
    while tid in TaskDict.keys():
        tid = rand_string(6).lower()
    
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
                    str(task.completed) + " " + str(task.delayed) + "\n")
    return

def modifytask(TaskList, TaskDict, tid):
    tid = tid.strip().lower()
    if not tid in TaskDict.keys():
        print("TID not found. Reloading")
        return
    task, listindex = TaskDict[tid]
    if TaskList[listindex] != task:
        print("Unknown Error. Quitting")
        return
    print(task.id, task.dtsoft, task.dthard, task.name, task.priority, task.completed, task.delayed)
    
    a = int(input("\n\n1. Toggle Completion\n2. Change name\n3. Change priority\n4. Delay task\n5. Return\n%> ") or 5)
    
    if a == 5:
        return
    
    if a == 1:
        task.togcomplete()
    if a == 2:
        task.name = input("Enter New Name: ") or task.name
    if a == 3:
        task.prioritise(int(input("Enter New Priority: ") or task.priority) - task.priority)
    if a == 4:
        b = int(input("Delay days: ") or 0)
        c = 3600 * int(input("Delay hours: ") or 0)
        c += 60 * int(input("Delay mins: ") or 0)
        c += int(input("Delay seconds: ") or 0)
        mode = int(input("Delay [1]Soft [2]Hard [3]Both: ") or 3)
        #skipadd = bool(int(input("Not add to count?") or 0))
        task.extend(timedelta(days=b, seconds=c), mode-1, skipadd=False)
    
    TaskList[listindex] = task
    TaskDict[tid] = (task, listindex)
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
        tid = objects[0]
        dtsoft = datetime.strptime(objects[1], "%y%m%dT%H%M")
        dthard = datetime.strptime(objects[2], "%y%m%dT%H%M")
        name = objects[3].replace("_", " ")
        priority = int(objects[4])
        completed = bool(objects[5] == "True")
        delayed = int(objects[6]) # times that it has been delayed

        NewTask = Task(tid, dtsoft, dthard, name, priority, completed, delayed)
    
        if tid in TaskDict.keys():
            print(f"Error loading task:\n{tid} {name}\nTID exists, skipping...")

        TaskList.append(NewTask)
        TaskDict[tid] = (NewTask, len(TaskList)-1) # store index

        item = f.readline()

withcomplete = False

while True:
    option = showtasks(TaskList, withcomplete)
    #print(option)
    if option == 0:
        continue
    if option == 1:
        withcomplete = not withcomplete
        continue
    if option == 2:
        TaskList, TaskDict = addtask(TaskList, TaskDict)
        continue
    if option == 3:
        TaskList, TaskDict = modifytask(TaskList, TaskDict, input("Enter tid: "))
        continue
    if option == 4:
        writetofile(TaskList, write)
        
    if option == 5:
        break
