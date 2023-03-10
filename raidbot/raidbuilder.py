import itertools
import time

from raidbot.database import get_player, get_player_by_id, get_player_by_name

TANKS = ["WAR", "PLD", "DRK", "GNB"]
HEALERS = ["WHM", "SCH", "AST", "SGE"]
MELEES = ["MNK", "DRG", "NIN", "SAM", "RPR"]
RANGED = ["BRD", "MCH", "DNC"]
CASTERS = ["BLM", "SMN", "RDM"]
LIMITED = ["BLU"]
DPS = [*MELEES, *RANGED, *CASTERS]
JOBS = [*TANKS, *HEALERS, *DPS]
CLASSES = ["MRD", "GLD", "CNJ", "ACN", "PGL", "LNC", "ROG", "ARC", "THM"]


def string_from_list(lt):
    ret_string = ""
    for n in lt:
        if n is not None:
            ret_string += n + ", "
    ret_string = ret_string[:-2]
    return ret_string


def job_string_to_list(job_string: str):
    return job_string.split(",")


class Character:
    """A Class defining a character.
    Note: Job_list should be given in Order of priority."""
    def __init__(self, discord_id: int, name: str, job_list: str, involuntary_benches: int):
        self.discord_id = discord_id
        self.character_name = name
        self.jobs = []
        if isinstance(job_list, str):
            self.set_jobs(job_string_to_list(job_list))
        else:
            self.set_jobs(job_list)

        self.benched = False  # set benched according to user preference or by force after deciding on final raid
        self.involuntary_benches = involuntary_benches

    def set_jobs(self, job_list):
        self.jobs = []
        for job in job_list:
            if job in JOBS and job not in self.jobs:
                self.jobs.append(job)
            elif job in self.jobs:
                raise SyntaxError(f"{job} already registered")
            elif job in CLASSES:
                raise SyntaxError(f"{job} is a class. Please be a responsible Warrior of Light and equip your "
                                  f"job/soul stone")
            else:
                raise SyntaxError(f"{job} is not a valid job")

    def get_overview_string(self):
        jobs_string = string_from_list(self.jobs)

        out = f"```\n" \
              f"Character name: {self.character_name}\n" \
              f"Jobs:           {jobs_string}\n" \
              f"This character is owned by @{self.discord_id}.```"
        return out


def make_character_from_db(conn, discord_id, name):
    if discord_id and not name:
        p = get_player_by_id(conn, discord_id)[0]
    elif name and not discord_id:
        p = get_player_by_name(conn, name)[0]
    else:
        p = get_player(conn, discord_id, name)[0]

    if p:
        return Character(p[1], p[2], p[3], p[6]), p[4], p[5]
    else:
        raise ValueError(f"No Character with id {discord_id} and name {name} found in db.")


def calc_composition_score(combination: tuple[Character], picked_jobs: tuple, n_tanks: int, n_healers: int, n_dps: int,
                           no_double_jobs=True, maximize_diverse_dps=True, use_benched_counter=True):
    # First checks - do we have the correct number of roles? if not, don't bother
    if sum(t in picked_jobs for t in TANKS) != n_tanks:
        score = 0
    elif sum(h in picked_jobs for h in HEALERS) != n_healers:
        score = 0
    elif sum(d in picked_jobs for d in DPS) != n_dps:
        score = 0
    else:
        job_prios = []
        for i, member in enumerate(combination):
            idx = member.jobs.index(picked_jobs[i])  # Combination and picked jobs must be in the correct order
            member_score = len(JOBS) - idx  # First job in list gets highest priority and so on
            if member.benched:  # member prefers to be on bench so we give him a lower priority
                member_score -= 8  # need to tweak weight?
            elif use_benched_counter:
                member_score += member.involuntary_benches  # add times benched to score
            job_prios.append(member_score)

        score = sum(job_prios)

        # Extra score boosts/detractors

        # Do we have duplicates?
        if no_double_jobs and len(picked_jobs) != len(set(picked_jobs)):
            score -= 8  # Weight here might need to be adjusted

        # Group DPS comp
        if maximize_diverse_dps:
            if sum(d in picked_jobs for d in MELEES) > 0:
                if sum(d in picked_jobs for d in RANGED) > 0:
                    if sum(d in picked_jobs for d in CASTERS) > 0:
                        # We have at least one of each type of DPS
                        score += 4
                    else:
                        # We have at least two different types of DPS
                        score += 2

                elif sum(d in picked_jobs for d in CASTERS) > 0:
                    # We have at least two different types of DPS
                    score += 2
            elif sum(d in picked_jobs for d in CASTERS) > 0 and sum(d in picked_jobs for d in RANGED) > 0:
                # We have at least two different types of DPS
                score += 2

        # TODO: add number of participated raids into calculation

    return score


def make_raid(characters: list[Character], n_tanks: int, n_healers: int, n_dps: int,
              no_double_jobs=True, maximize_diverse_dps=True, use_benched_counter=True):
    """Given a list of Characters, this will form the most desirable possible raid composition"""
    n_raiders = n_tanks + n_healers + n_dps

    # If not enough raiders are given, we might as well stop here
    if len(characters) < n_raiders:
        print("Not enough participants")
        return None

    groups_comps_and_scores = []
    # Iterate through all possible combinations of the given number of players
    for group in itertools.combinations(characters, n_raiders):
        # Get all jobs for each member of this combination in one list of lists
        job_lists = []
        for member in group:
            job_lists.append(member.jobs)

        # Get all possible job combinations
        comps = itertools.product(*job_lists)

        # Iterate over comps and get scores
        for comp in comps:
            score = calc_composition_score(group, comp, n_tanks, n_healers, n_dps,
                                           no_double_jobs, maximize_diverse_dps, use_benched_counter)
            if score > 0:  # only append viable combinations
                groups_comps_and_scores.append([group, comp, score])

    # We find the best comp by looking for the max score
    best = max(groups_comps_and_scores, key=lambda x: x[2])

    # Get list of best raids if there are multiple
    best_score = best[2]
    all_bests = [raid for raid in groups_comps_and_scores if raid[2] == best_score]

    # Statistics, out of curiosity, comment out later:
    # stat_str = f"There are {len(groups_comps_and_scores)} viable combinations.\n" \
    #            f"Best score of {best_score} appears {len(all_bests)} times."

    return all_bests  # , stat_str


if __name__ == '__main__':
    # Test raidbuilder functionality
    participants = [
        Character(1, "Nama Zu",     "GNB,PLD,MCH", 1),
        Character(2, "Na Mazu",     "DRK,GNB,MNK", 0),
        Character(3, "Zu Nama",     "WHM,AST,PLD,BRD", 0),
        Character(4, "Zuna Ma",     "BLM,SMN,RDM,SCH", 0),
        Character(5, "Mama Zu",     "BRD,WHM,RDM", 0),
        Character(6, "Uza Man",     "MNK,SAM,GNB", 0),
        Character(7, "Zuzu Nana",   "DNC", 0),
        Character(8, "Yes Yes",     "PLD,WAR,MCH,DNC", 0),
        Character(9, "Dummy Thicc", "BLM,SAM", 0),
        Character(10, "Blue Chicken", "WHM,SMN", 0),
        Character(11, "Ragu Bolognese", "DRG,NIN", 0)
    ]

    participants[9].benched = True
    participants[2].benched = True
    participants[3].benched = True

    # Checking how long this takes
    begin = time.time()

    # Get X best raids
    best_raids = make_raid(participants, 2, 2, 4)

    end = time.time()
    print(f"Calculations took {end-begin} seconds.")

    # Print Names in order
    print([p.character_name for p in participants])

    # Print Composition in order of Names (Bench is indicated by ---)
    for group, comp, score in best_raids:
        print_line = []
        for player in participants:
            if player in group:
                print_line.append(comp[group.index(player)])
            else:
                print_line.append('---')
        print(print_line)

