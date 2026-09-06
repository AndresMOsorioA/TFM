import numpy as np
import heapq
from datetime import datetime, timedelta
import random
from copy import deepcopy
from collections import Counter, defaultdict
import heapq
from datetime import datetime, timedelta
import random
from copy import deepcopy
from collections import Counter, defaultdict


# ---------------- TIME HELPER ----------------
def t(base_date, hhmm):
    h, m = map(int, hhmm.split(":"))
    return base_date.replace(hour=h, minute=m, second=0, microsecond=0)

# ---------------- CALL ----------------
class Call:
    def __init__(self, arrival_time, duration, language):
        self.arrival_time = arrival_time
        self.duration = duration
        self.language = language

        r = np.random.rand()
        if r < 0.10:
            self.patience = np.random.exponential(20)
        elif r < 0.90:
            self.patience = np.random.exponential(60)
        else:
            self.patience = np.random.exponential(120)

        self.start_time = None
        self.end_time = None
        self.abandoned = False

# ---------------- AGENT ----------------
class Agent:
    def __init__(self, agent_id, languages, active_periods):
        self.agent_id = agent_id
        self.languages = languages
        self.active_periods = active_periods
        self.available_at = datetime.min
        self.calls_handled = []

    def can_handle(self, call):
        return call.language in self.languages

    def is_active(self, current_time):
        return any(start <= current_time < end for start, end in self.active_periods)

    def assign_call(self, call, current_time):
        call.start_time = current_time
        call.end_time = current_time + timedelta(minutes=call.duration)
        self.available_at = call.end_time
        self.calls_handled.append(call)

# ---------------- SYSTEM ----------------
class CallCenter:
    def __init__(self, agents):
        self.agents = agents
        self.queue = []
        self.calls = []
        self.events = []
        self.counter = 0

    def schedule(self, t, etype, call=None):
        self.counter += 1
        heapq.heappush(self.events, (t, self.counter, etype, call))

    def get_lambda(self, t, lambdas):
        return lambdas[t.hour]

    def generate(self, start, hours, lambdas):
        end = start + timedelta(hours=hours)

        langs = ["EN","ES","FR","AR"]
        lw = [0.5, 0.4, 0.05, 0.05]
        types = [4, 6.5, 15]
        tw = [0.2,0.5,0.3]

        current_time = start

        while current_time < end:
            lam = self.get_lambda(current_time, lambdas) / 60
            current_time += timedelta(seconds=np.random.exponential(1/lam) * 60)

            if current_time >= end:
                break

            call = Call(
                current_time,
                random.choices(types, tw)[0],
                random.choices(langs, lw)[0]
            )

            self.calls.append(call)
            self.schedule(call.arrival_time, "arr", call)

    def run(self):
        while self.events:
            t_event, _, etype, call = heapq.heappop(self.events)

            if etype == "arr":
                self.queue.append(call)

                self.schedule(
                    call.arrival_time + timedelta(seconds=call.patience),
                    "ab",
                    call
                )

                self.assign(t_event)

            elif etype == "ab":
                if call in self.queue:
                    call.abandoned = True
                    self.queue.remove(call)

            elif etype == "fin":
                self.assign(t_event)

    def assign(self, current_time):
        active_agents = [a for a in self.agents if a.is_active(current_time)]
        free_agents = [a for a in active_agents if a.available_at <= current_time]

        free_agents.sort(
            key=lambda a: (current_time - a.available_at).total_seconds(),
            reverse=True
        )

        for agent in free_agents:
            for i, call in enumerate(self.queue):
                if agent.can_handle(call):
                    self.queue.pop(i)
                    agent.assign_call(call, current_time)
                    self.schedule(call.end_time, "fin", call)
                    break

# ---------------- ONE SIM ----------------
def random_languages():
    language_pool = ["EN", "ES", "FR", "AR"]
    lang_count = np.random.choice([2], p=[1])
    chosen = random.sample(language_pool, k=lang_count)
    if "EN" not in chosen and np.random.rand() < 0.9:
        chosen[0] = "EN"
    if "FR" not in chosen and np.random.rand() < 0.5:
        chosen[1] = "ES"
    return sorted(set(chosen))

def random_shift_periods(base_date):
    shift_length = np.random.choice([4, 5, 8], p=[0.1, 0.2, 0.7])
    if shift_length == 8:
        start_hour = np.random.choice([8,9,10,11,12,13,14],p=[0.4, 0.05, 0.05, 0.0, 0.05, 0.05, 0.4])
    elif shift_length == 5:
        start_hour = np.random.choice([8,9,16,17],p=[0.25,0.25,0.25,0.25])
    else:
        start_hour = np.random.choice([8,9,10,16,17,18],p=[0.1,0.2,0.2,0.2,0.2,0.1])
    end_hour = start_hour + shift_length

    if shift_length >= 6:
        break_length = 30
        break_start_hour = start_hour + random.choice(range(4, 5))
        break_start_min = random.choice([0, 30])

        shift_start = base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        shift_end = base_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        break_start = base_date.replace(hour=break_start_hour, minute=break_start_min, second=0, microsecond=0)
        break_end = break_start + timedelta(minutes=break_length)

        breaks = [(break_start, break_end)]

        for _ in range(3):
            b = shift_start + timedelta(
        minutes=random.randint(0, int((shift_end - shift_start).total_seconds() / 60) - 5)
    )
            breaks.append((b, b + timedelta(minutes=5)))

        breaks.sort()

        periods = []
        current = shift_start

        for b_start, b_end in breaks:
            if current < b_start:
                periods.append((current, b_start))
            current = b_end
        
        if current < shift_end:
            periods.append((current, shift_end))
        return periods
    
    return [(
        base_date.replace(hour=start_hour, minute=0, second=0, microsecond=0),
        base_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    )]

def generate_random_agents(base_date, min_agents=0, max_agents=100):
    agent_total = random.randint(min_agents, max_agents)
    return [
        Agent(agent_id + 1, random_languages(), random_shift_periods(base_date))
        for agent_id in range(agent_total)
    ]

def run_once(agents):

    base = datetime(2026,4,3)

    cc = CallCenter(agents)

    start = t(base,"08:00")
    lambdas = [0,0,0,0,0,0,0,0,40,50,60,70,60,60,70,70,60,60,60,60,50,40]

    cc.generate(start, 14, lambdas)
    cc.run()

    total = len(cc.calls)
    answered = sum(1 for c in cc.calls if not c.abandoned)
    answer_rate = answered / total if total else 0

    lang_total = Counter(c.language for c in cc.calls)
    lang_ans = Counter(c.language for c in cc.calls if not c.abandoned)
    answer_rate_lang = {k: lang_ans[k]/lang_total[k] for k in lang_total}

    hourly = defaultdict(lambda: [0,0])
    for c in cc.calls:
        h = c.arrival_time.replace(minute=0, second=0, microsecond=0)
        hourly[h][1] += 1
        if not c.abandoned:
            hourly[h][0] += 1

    agent_occ = {}
    total_busy = 0
    total_active = 0

    for a in agents:
        busy = sum((c.end_time - c.start_time).total_seconds() for c in a.calls_handled)
        active = sum((e - s).total_seconds() for s,e in a.active_periods)

        agent_occ[a.agent_id] = busy/active if active else 0

        total_busy += busy
        total_active += active

    global_occ = total_busy / total_active if total_active else 0

    hourly_busy = defaultdict(float)
    hourly_capacity = defaultdict(float)

    for a in agents:
        for c in a.calls_handled:
            s,e = c.start_time, c.end_time
            cur = s
            while cur < e:
                h = cur.replace(minute=0, second=0, microsecond=0)
                h_end = h + timedelta(hours=1)
                overlap = min(e,h_end) - max(cur,h)
                if overlap.total_seconds()>0:
                    hourly_busy[h]+=overlap.total_seconds()
                cur = h_end

    for a in agents:
        for s,e in a.active_periods:
            cur = s
            while cur < e:
                h = cur.replace(minute=0, second=0, microsecond=0)
                h_end = h + timedelta(hours=1)
                overlap = min(e,h_end) - max(cur,h)
                if overlap.total_seconds()>0:
                    hourly_capacity[h]+=overlap.total_seconds()
                cur = h_end

    system_hourly_occ = {
        h: hourly_busy[h]/hourly_capacity[h] if hourly_capacity[h] else 0
        for h in hourly_capacity
    }

    return answer_rate, answer_rate_lang, hourly, agent_occ, system_hourly_occ, global_occ



import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def pareto_front(points):

    front = []

    for i,p in enumerate(points):

        dominated = False

        for j,q in enumerate(points):

            if i == j:
                continue

            if (
                q[0] >= p[0] and
                q[1] >= p[1] and
                (q[0] > p[0] or q[1] > p[1])
            ):
                dominated = True
                break

        if not dominated:
            front.append(i)

    return front


def montecarlo(n=50, repeticiones=1):

    base = datetime(2026,4,3)

    occ_history = []
    ar_history = []
    agents_history = []

    for i in range(n):

        # Generar UN solo workforce
        workforce = generate_random_agents(
            base,
            min_agents=20,
            max_agents=40
        )

        occs = []
        ars = []

        # Evaluarlo 20 veces
        for _ in range(repeticiones):

            ar, _, _, _, _, occ = run_once(deepcopy(workforce))

            ars.append(ar)
            occs.append(occ)

        # Guardar el promedio del workforce
        occ_history.append(np.mean(occs))
        ar_history.append(np.mean(ars))
        agents_history.append(len(workforce))

        if (i + 1) % 100 == 0:
            print(f"Workforces evaluated: {i+1}/{n}")

    return occ_history, ar_history, agents_history


def plot_pareto(occ,ar):


    fig,ax = plt.subplots(figsize=(11,8))

    ax.scatter(
        occ,
        ar,
        color="blue",
        alpha=0.25,
        s=25
    )

    pts = list(zip(occ,ar))

    front = pareto_front(pts)

    ax.scatter(
        np.array(occ)[front],
        np.array(ar)[front],
        edgecolors="black",
        linewidth=1,
        s=90
    )

    sm = plt.cm.ScalarMappable(
        
        norm=plt.Normalize(
            0,
            len(occ)-1
        )
    )

    sm.set_array([])


    ax.set_xlabel("Occupancy")

    ax.set_ylabel("Answer Rate")

    ax.set_title(
        "Monte Carlo Pareto Front"
    )

    ax.grid(True)

    plt.show()


occ, ar, nagents = montecarlo(
    n=50,
    repeticiones=1
)

print("\n==================== MONTE CARLO RESULTS ====================\n")

print(f"Simulations: {len(occ)}")

print("\nANSWER RATE")
print(f"   Min : {min(ar):.2%}")
print(f"   Max : {max(ar):.2%}")
print(f"   Mean: {np.mean(ar):.2%}")

print("\nOCCUPANCY")
print(f"   Min : {min(occ):.2%}")
print(f"   Max : {max(occ):.2%}")
print(f"   Mean: {np.mean(occ):.2%}")

print("\nNUMBER OF AGENTS")
print(f"   Min : {min(nagents)}")
print(f"   Max : {max(nagents)}")
print(f"   Mean: {np.mean(nagents):.2f}")

print("\n=============================================================\n")
plot_pareto(
    occ,
    ar
)
