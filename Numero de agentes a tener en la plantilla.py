import random
from collections import Counter

# PARAMETERS

REQUIRED_AGENTS = 14       # for results in the article, multiple this number by two as there are 2 shifts per day.
TARGET_COVERAGE = 0.8       

# Annual vacation entitlement
VACATION_DAYS_PER_YEAR = 38

# Daily probabilities when scheduled
SICK_PROB = 0.05
TRAINING_PROB = 0.1

SIM_YEARS = 1000

# DAYS

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

DAY_NAMES = [
    "Mon", "Tue", "Wed",
    "Thu", "Fri", "Sat", "Sun"
]

# COVERAGE DAYS

COVERAGE_DAYS = {
    MON,
    TUE,
    WED,
    THU,
    FRI
}

# WEEKEND ROTATION

TEAM_WEEKENDS_OFF = {
    "A": {0, 1},   
    "B": {1, 2},  
    "C": {2, 3},   
    "D": {3, 0},   
}

# WEEKDAY OFF PATTERNS

WEEKDAY_OFF_PATTERNS = [
    (MON, TUE),
    (TUE, WED),
    (WED, THU),
    (THU, FRI),
    (MON, FRI)
]

# EMPLOYEE

class Employee:

    def __init__(self, team, weekday_pattern):

        self.team = team
        self.weekday_pattern = weekday_pattern

        # Generate annual vacation days
        self.vacation_days = set(
            random.sample(
                range(365),
                VACATION_DAYS_PER_YEAR
            )
        )

    def scheduled_to_work(self, week_in_cycle, day):

        weekend_off = (
            week_in_cycle
            in TEAM_WEEKENDS_OFF[self.team]
        )

        # Weekend off week

        if weekend_off:

            return day in [
                MON, TUE, WED,
                THU, FRI
            ]

        # Weekend working week

        return day not in self.weekday_pattern

    def available(
        self,
        week_in_cycle,
        day,
        day_of_year
    ):

        if not self.scheduled_to_work(
            week_in_cycle,
            day
        ):
            return False

        # Vacation

        if day_of_year in self.vacation_days:
            return False

        # Sick

        if random.random() < SICK_PROB:
            return False

        # Training

        if random.random() < TRAINING_PROB:
            return False

        return True

# BUILD BALANCED WORKFORCE

def build_workforce(headcount):

    employees = []

    teams = ["A", "B", "C", "D"]

    # -------------------------
    # Split evenly across teams
    # -------------------------

    base_team = headcount // len(teams)
    extra_team = headcount % len(teams)

    team_sizes = []

    for i in range(len(teams)):

        n = base_team

        if i < extra_team:
            n += 1

        team_sizes.append(n)

    for team, team_size in zip(
        teams,
        team_sizes
    ):

        base_pattern = (
            team_size //
            len(WEEKDAY_OFF_PATTERNS)
        )

        extra_pattern = (
            team_size %
            len(WEEKDAY_OFF_PATTERNS)
        )

        for p_idx, pattern in enumerate(
            WEEKDAY_OFF_PATTERNS
        ):

            n = base_pattern

            if p_idx < extra_pattern:
                n += 1

            for _ in range(n):

                employees.append(
                    Employee(
                        team,
                        pattern
                    )
                )

    return employees

# SIMULATION

def evaluate_headcount(headcount):

    employees = build_workforce(headcount)

    successful_days = 0
    total_days = 0

    daily_available = []

    weekday_sum = Counter()
    weekday_count = Counter()

    for _ in range(SIM_YEARS):

        for week in range(52):

            week_in_cycle = week % 4

            for day in range(7):

                day_of_year = week * 7 + day

                available = sum(

                    emp.available(
                        week_in_cycle,
                        day,
                        day_of_year
                    )

                    for emp in employees
                )

                daily_available.append(
                    available
                )

                weekday_sum[day] += available
                weekday_count[day] += 1

                if day in COVERAGE_DAYS:

                    if available >= REQUIRED_AGENTS:
                        successful_days += 1

                    total_days += 1

    coverage = (
        successful_days /
        total_days
    )

    avg_available = (
        sum(daily_available)
        / len(daily_available)
    )

    min_available = min(
        daily_available
    )

    weekday_average = {

        DAY_NAMES[d]:
        weekday_sum[d]
        / weekday_count[d]

        for d in range(7)
    }

    return (
        coverage,
        avg_available,
        min_available,
        weekday_average
    )

# SEARCH

for headcount in range(
    REQUIRED_AGENTS,
    100
):

    (
        coverage,
        avg_avail,
        worst_day,
        weekday_avg
    ) = evaluate_headcount(
        headcount
    )

    print(
        f"Headcount={headcount:2d} "
        f"Coverage={coverage:.2%}"
    )

    if coverage >= TARGET_COVERAGE:

        print("\n===================================")
        print("RESULT")
        print("===================================")

        print(
            f"Required available agents : "
            f"{REQUIRED_AGENTS}"
        )

        print(
            f"Target coverage           : "
            f"{TARGET_COVERAGE:.0%}"
        )

        print(
            f"Coverage days             : "
            f"Mon Tue Wed Thu Fri"
        )

        print(
            f"Required headcount        : "
            f"{headcount}"
        )

        print(
            f"Coverage achieved         : "
            f"{coverage:.2%}"
        )

        print(
            f"Average available         : "
            f"{avg_avail:.2f}"
        )

        print(
            f"Worst day observed        : "
            f"{worst_day}"
        )

        print("\nAVERAGE AVAILABLE BY DAY")

        for day in DAY_NAMES:

            print(
                f"{day}: "
                f"{weekday_avg[day]:.2f}"
            )

        break