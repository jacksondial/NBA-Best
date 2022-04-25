"""Build and compile model."""
import sqlite3
from itertools import combinations, product

con = sqlite3.connect("nba.db")

cur = con.cursor()


def get_max(column: str, position: str):
    "Get max value for a given variable."
    max = cur.execute(
        f"""
        SELECT MAX({column}) FROM PlayerStats
        WHERE GamesPlayed > 15
        AND ThreePointersAttempted > 2
        AND Position IN ({position})
        """,
        # The ThreePointersAttempted variable is actually the average number of
        # 3 pointers attempted per game, so I decied that 2 was a reasonable
        # average to reduce an individual playing in just a few games and
        # hitting most of his 3's
    )
    return max.fetchone()[0]


# print(get_max("ThreePointersPct"))
# print(get_max("Assists"))
# print(get_max("Turnovers"))
# print("start")
# test_pos = "'PG', 'SG'"
# print(get_max("TwoPointersAttempted", test_pos))
# print(get_max("TwoPointersPct", test_pos))

# attempt2 = cur.execute("SELECT Name FROM PlayerStats WHERE TwoPointersAttempted = 16.2")
# print(attempt2.fetchone())

# the highest 2ptPct is .673, Matisse Thybulle, but his avg 2pAttempt is only
# 2.4.... should I include him?
# I think it is actually ok because we are also multiplying by the number of 2
# pointers made, so his score wont actually be the highest (likely)

# pct2 = cur.execute(
#     "SELECT Name, TwoPointersAttempted FROM PlayerStats WHERE TwoPointersPct = .673"
# )
# print(pct2.fetchone())

# My idea is to normalize each of the metrics by the maximum value in all of
# the data, since this is a competition then we can compare individuals to
# others

# The argument could be made that since we are selecting players by position,
# then we should normalize by the max for a specific metric only among players
# in that same position, which is very fair. BUT I am going to start more
# simple than that.

# UPDATE: I added in the funcitonality to only include players in that position
# for the maximum calculation.

# ass_turn = cur.execute(
#     """SELECT Name FROM PlayerStats WHERE (Assists / Turnovers) > 7 AND
#     GamesPlayed > 15 AND ThreePointersAttempted > 2"""
# )
# print(ass_turn.fetchall())

# tyus_jones = cur.execute(
#     """SELECT
#         GamesPlayed,
#         Assists,
#         Turnovers
#     FROM PlayerStats WHERE Name = 'Tyus Jones'
#     """
# )
# print(tyus_jones.fetchone())

###############################################################################
# Guards
###############################################################################


def guard_normalize_query(position: str):
    """Create columns that are normalized."""
    query = f"""
        CREATE TABLE GuardsNormalizedStats AS
            SELECT
                ps.Name,
                Position,
                ROUND(ThreePointersAttempted  * ThreePointersPct /
                    {get_max("ThreePointersAttempted * ThreePointersPct",
                    position)},3) AS j_threes,
                ROUND((Assists / Turnovers) / {get_max("Assists / Turnovers",
                    position)},3) AS j_atr,
                ROUND(Steals / {get_max("Steals", position)}, 3) AS j_stl,
                ROUND(OffensiveRebounds / {get_max("OffensiveRebounds",
                    position)}, 3) AS j_or,
                ROUND((FreeThrowsAttempted * FreeThrowPct) /
                    {get_max("FreeThrowsAttempted * FreeThrowPct",
                    position)},3) AS j_ft,
                ROUND((TwoPointersAttempted * TwoPointersPct) /
                    {get_max("TwoPointersAttempted * TwoPointersPct",
                    position)},3) AS j_twos,
                ROUND(("Points") / {get_max("Points", position)}) AS j_points
            FROM PlayerStats ps
            LEFT JOIN Salary s
            ON ps.Name = s.Name
            WHERE ps.Position IN ({position})
            AND GamesPlayed > 15
            AND ThreePointersAttempted > 2
            ORDER BY s.Salary2122
            """
    return query


cur.execute("DROP TABLE IF EXISTS GuardsNormalizedStats")
# print(guard_normalize_query("'PG', 'SG'"))
cur.execute(guard_normalize_query("'PG', 'SG'"))
con.commit()

# This was useful before I created the table as the select statement
# guards = cur.execute(normalize_query("'PG', 'SG'"))
# for i in guards:
#     print(i)
# guards = cur.execute("SELECT * FROM GuardsNormalizedStats")
# for i in guards:
#     print(i)


def guard_selections(
    table: str,
    number_players: int,
    w1: float,
    w2: float,
    w3: float,
    w4: float,
    w5: float,
    w6: float,
    w7: float,
):
    "Make Selections."
    query = f"""
    SELECT
        Name,
        ({w1} * j_threes) + ({w2} * j_atr) + ({w3} * j_stl) + ({w4} * j_or) +
        ({w5} * j_ft) + ({w6} * j_twos) + ({w7} * j_points) AS rank
    FROM {table}
    ORDER BY rank DESC
    LIMIT {number_players}
    """
    return query


top5 = []
guard_ranked = cur.execute(
    guard_selections("GuardsNormalizedStats", 2, 3, 3, 2, 1, 4, 2, 3)
)
for i in guard_ranked:
    top5.append(i[0])
    print(i)
print("break")


###############################################################################
# Forwards
###############################################################################


def forward_normalize_query(position: str):
    "Create columns that are normalized"
    query = f"""
        CREATE TABLE ForwardsNormalizedStats AS
            SELECT
                ps.Name,
                Position,
                ROUND(ThreePointersAttempted  * ThreePointersPct /
                    {get_max("ThreePointersAttempted * ThreePointersPct",
                    position)},3) AS j_threes,
                ROUND((Assists / Turnovers) / {get_max("Assists / Turnovers",
                    position)},3) AS j_atr,
                ROUND(DefensiveRebounds / {get_max("DefensiveRebounds",
                    position)}, 3) AS j_dr,
                ROUND(OffensiveRebounds / {get_max("OffensiveRebounds",
                    position)}, 3) AS j_or,
                ROUND((FreeThrowsAttempted * FreeThrowPct) /
                    {get_max("FreeThrowsAttempted * FreeThrowPct",
                    position)},3) AS j_ft,
                ROUND((TwoPointersAttempted * TwoPointersPct) /
                    {get_max("TwoPointersAttempted * TwoPointersPct",
                    position)},3) AS j_twos,
                ROUND(Blocks / {get_max("Blocks", position)}, 3) AS j_blocks,
                ROUND(Points / {get_max("Points", position)}, 3) AS j_points
            FROM PlayerStats ps
            LEFT JOIN Salary s
            ON ps.Name = s.Name
            WHERE ps.Position IN ({position})
            AND GamesPlayed > 15
            AND ThreePointersAttempted > 2
            ORDER BY s.Salary2122
            """
    return query


cur.execute("DROP TABLE IF EXISTS ForwardsNormalizedStats")
cur.execute(forward_normalize_query("'PF', 'SF'"))
con.commit()


def forward_selections(
    table: str,
    number_players: int,
    w1: float,
    w2: float,
    w3: float,
    w4: float,
    w5: float,
    w6: float,
    w7: float,
    w8: float,
):
    "Make Selections."
    query = f"""
    SELECT
        Name,
        ({w1} * j_threes) + ({w2} * j_atr) + ({w3} * j_dr) + ({w4} * j_or) +
        ({w5} * j_ft) + ({w6} * j_twos) + ({w7} * j_blocks) + ({w8} *j_points)
            AS rank
    FROM {table}
    ORDER BY rank DESC
    LIMIT {number_players}
    """
    return query


forward_ranked = cur.execute(
    forward_selections("ForwardsNormalizedStats", 2, 2, 2, 3, 3, 3, 3, 4, 3)
)
for i in forward_ranked:
    top5.append(i[0])
    print(i)
print("break")

# testing = cur.execute(
#     "SELECT COUNT(Name) FROM PlayerStats WHERE Position IN ('PF', 'SF')"
# )
# for i in testing:
#     print(i)


###############################################################################
# Centers
###############################################################################


def center_normalize_query(position: str):
    "Create columns that are normalized"
    query = f"""
        CREATE TABLE CentersNormalizedStats AS
            SELECT
                ps.Name,
                Position,
                ROUND((Assists / Turnovers) / {get_max("Assists / Turnovers",
                    position)},3) AS j_atr,
                ROUND(DefensiveRebounds / {get_max("DefensiveRebounds",
                    position)}, 3) AS j_dr,
                ROUND(OffensiveRebounds / {get_max("OffensiveRebounds",
                    position)}, 3) AS j_or,
                ROUND((FreeThrowsAttempted * FreeThrowPct) /
                    {get_max("FreeThrowsAttempted * FreeThrowPct",
                    position)},3) AS j_ft,
                ROUND((TwoPointersAttempted * TwoPointersPct) /
                    {get_max("TwoPointersAttempted * TwoPointersPct",
                    position)},3) AS j_twos,
                ROUND(Blocks / {get_max("Blocks", position)}, 3) AS j_blocks,
                ROUND(Points / {get_max("Points", position)}, 3) AS j_points
            FROM PlayerStats ps
            LEFT JOIN Salary s
            ON ps.Name = s.Name
            WHERE ps.Position IN ({position})
            AND GamesPlayed > 15
            AND ThreePointersAttempted > 2
            ORDER BY s.Salary2122
            """
    return query


cur.execute("DROP TABLE IF EXISTS CentersNormalizedStats")
cur.execute(center_normalize_query("'C'"))
con.commit()


def center_selections(
    table: str,
    number_players: int,
    w1: float,
    w2: float,
    w3: float,
    w4: float,
    w5: float,
    w6: float,
    w7: float,
):
    "Make Selections."
    query = f"""
    SELECT
        Name,
        ({w1} * j_atr) + ({w2} * j_dr) + ({w3} * j_or) + ({w4} * j_ft) +
        ({w5} * j_twos) + ({w6} * j_blocks) + ({w7} * j_points) AS rank
    FROM {table}
    ORDER BY rank DESC
    LIMIT {number_players}
    """
    return query


center_ranked = cur.execute(
    center_selections("CentersNormalizedStats", 1, 7, 3, 5, 8, 2, 4, 4)
)
for i in center_ranked:
    top5.append(i[0])
    print(i)

salaryTop5 = []
for i in top5:
    salary = cur.execute(f"SELECT Salary2122 FROM Salary WHERE Name = '{i}'")
    for j in salary:
        salaryTop5.append(j[0])


def get_position_combinations(
    type: str, numPlayers: int, numInLineup: int, salaryYear: int
):
    name = []
    rating = []
    if type == "guard":
        data = cur.execute(guard_selections("GuardsNormalizedStats", numPlayers))
    elif type == "forward":
        data = cur.execute(forward_selections("ForwardsNormalizedStats", numPlayers))
    elif type == "center":
        data = cur.execute(center_selections("CentersNormalizedStats", numPlayers))

    for i in data:
        name.append(i[0])
        rating.append(i[1])

    salary = []
    for i in name:
        player_salary = cur.execute(
            f"SELECT Salary{salaryYear} FROM Salary WHERE Name = '{i}'"
        )
        for j in player_salary:
            salary.append(j[0])

    name_combos = list(combinations(name, numInLineup))

    rating_combos = list(combinations(rating, numInLineup))
    rating_combo_sum = []
    for i in rating_combos:
        rating_combo_sum.append(sum(i))

    salary_combos = list(combinations(salary, numInLineup))
    salary_combo_sum = []
    for i in salary_combos:
        salary_combo_sum.append(sum(i))

    all_data = [name_combos, rating_combo_sum, salary_combo_sum]

    return all_data


# print(get_position_combinations("forward", 40, 1, 2122))


def select_lineup(
    num_guard: int, num_forward: int, num_center: int, salaryYear: int, budget: float
):
    num_combo = 5
    output = []
    while output == []:
        if num_combo == 40:
            print("Invalid input. Please try a higher budget or change a field.")
            break

        guards = get_position_combinations("guard", num_combo, num_guard, salaryYear)
        forwards = get_position_combinations(
            "forward", num_combo, num_forward, salaryYear
        )
        centers = get_position_combinations("center", num_combo, num_center, salaryYear)
        num_combo += 1

        all_name = [guards[0], forwards[0], centers[0]]
        all_name_combos = list(product(*all_name))

        all_salary = [guards[2], forwards[2], centers[2]]
        all_salary_combos = list(product(*all_salary))
        all_salary_combos_sum = []
        for i in all_salary_combos:
            all_salary_combos_sum.append(sum(i))

        salary_index = []
        for i in range(len(all_salary_combos_sum)):
            if all_salary_combos_sum[i] < (budget * 1000000):
                salary_index.append(i)

        if salary_index == []:
            continue

        all_rating = [guards[1], forwards[1], centers[1]]
        all_rating_combos = list(product(*all_rating))
        all_rating_combos_sum = []
        for i in all_rating_combos:
            all_rating_combos_sum.append(sum(i))

        best_index = 0
        best_rating = 0
        for i in salary_index:
            if all_rating_combos_sum[i] > best_rating:
                best_rating = all_rating_combos_sum[i]
                best_index = i

        output = [all_name_combos[best_index], all_salary_combos_sum[best_index]]

    return output
