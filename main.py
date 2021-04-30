import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from collections import defaultdict
from cmap import cmap
from east_west import east_west
import argparse


def parse_record(record: str) -> float:
    [wins, losses] = record.split('-')
    return int(wins) / int(losses)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--conference', default="")
    args = parser.parse_args()

    standings = pd.read_csv('standings.csv')
    standings = standings.set_index('Team')

    strength_of_schedule = defaultdict(list)

    games_in_may = pd.read_csv('may.csv')

    for _, game in games_in_may.iterrows():
        # determine strength of opponents
        home = game['Home/Neutral']
        vistor = game['Visitor/Neutral']

        strength_of_schedule[home].append(
            parse_record(standings['Overall'][vistor]))
        strength_of_schedule[vistor].append(
            parse_record(standings['Overall'][home]))

    for team in strength_of_schedule:
        # only keep final 8 games
        strength_of_schedule[team] = strength_of_schedule[team][-8:]

    for team in strength_of_schedule:
        # compute rolling strength of schedule
        for idx, game in enumerate(strength_of_schedule[team]):
            if idx > 0:
                strength_of_schedule[team][idx] += strength_of_schedule[team][idx-1]

    filtered_strength_of_schedule = {}

    if args.conference:  # optionally filter based on conference
        for team in strength_of_schedule:
            if east_west[team] == args.conference:
                filtered_strength_of_schedule[team] = strength_of_schedule[team]
    else:
        filtered_strength_of_schedule = strength_of_schedule

    strength_of_schedule_df = pd.DataFrame(
        filtered_strength_of_schedule).transpose()

    for i in range(0, 8):
        # rank based on strength of schedule
        strength_of_schedule_df['rank' +
                                str(i)] = strength_of_schedule_df[i].rank(method='first')

    # teams ordered by strength of schedule (8 games to go)
    teams_start = strength_of_schedule_df.index.tolist()
    teams_start.sort(key=lambda x: strength_of_schedule_df['rank0'][x])
    teams_start = [t.split()[-1] + ' (' + str(len(teams_start)-idx) + ')'
                   for idx, t in enumerate(teams_start)]

    # teams ordered by strength of schedule (end of regular season)
    teams_end = strength_of_schedule_df.index.tolist()
    teams_end.sort(key=lambda x: strength_of_schedule_df['rank7'][x])
    teams_end = [t.split()[-1] + ' (' + str(len(teams_end)-idx) + ')' for idx,
                 t in enumerate(teams_end)]

    fig, ax1 = plt.subplots()

    for _, row in strength_of_schedule_df.iterrows():
        # plot points
        x = np.arange(8)
        y = np.array(row.tolist()[-8:])
        ax1.scatter(x, y, c=cmap[row.name], s=150)

        # plot smooth connecting lines
        x_linspace = np.linspace(x.min(), x.max(), 500)
        f = interp1d(x, y, kind='quadratic')
        y_smooth = f(x_linspace)
        ax1.plot(x_linspace, y_smooth, c=cmap[row.name], lw=2)

    # bottom axis labels
    ax1.set_xticks(np.arange(0, 8))
    ax1.set_xticklabels(np.flip(np.arange(1, 9)),
                        font='Franklin Gothic Book', fontsize=12)
    ax1.set_xlabel('Games remaining', font='Franklin Gothic Book', fontsize=16)

    # left side axis labels
    ax1.set_yticks(np.arange(1, len(teams_start) + 1))
    ax1.set_yticklabels(teams_start, font='Franklin Gothic Book', fontsize=12)
    ax1.set_ylabel('Strength of schedule: 1 = hardest, 30 = easiest',
                   font='Franklin Gothic Book', fontsize=16)

    ax2 = ax1.twinx()  # secondary axis

    for _, row in strength_of_schedule_df.iterrows():
        # plot points on secondary axis, but make the lines and points transparent
        # hacky solution to make left and right axes align properly
        x = np.arange(8)
        y = np.array(row.tolist()[-8:])
        ax2.scatter(x, y, alpha=0)

        x_linspace = np.linspace(x.min(), x.max(), 500)
        f = interp1d(x, y, kind='quadratic')
        y_smooth = f(x_linspace)
        ax2.plot(x_linspace, y_smooth, alpha=0)

    # right side axis labels
    ax2.set_yticks(np.arange(1, len(teams_end) + 1))
    ax2.set_yticklabels(teams_end, font='Franklin Gothic Book', fontsize=12)

    title_extra = ''

    if args.conference == 'W':
        title_extra = ' (Western Conference)'
    if args.conference == 'E':
        title_extra = ' (Eastern Conference)'

    plt.title('2020-2021 NBA Season: Strength of Schedule Over Last 8 Games' + title_extra,
              font='Franklin Gothic Book', fontsize=20)
    plt.show()
