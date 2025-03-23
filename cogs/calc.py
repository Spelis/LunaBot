import math
import random

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands


class Calculations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.description = "Math Commands: Graphing, Latex, Evaluation"
        self.emoji = "🧮"

    @commands.hybrid_command("latex")
    async def latex(self, ctx, latex: str = ""):
        """Render LaTeX"""
        # check if the message contains an attachment (higher priority than the argument)
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            latex = await attachment.read()
            latex = latex.decode("utf-8")
        plt.rcParams["text.usetex"] = self.bot.usetex
        plt.rcParams["text.latex.preamble"] = r"\usepackage{stix}"
        fig = plt.figure(figsize=(3, 1), facecolor="#11111b")
        ax = plt.axes([0, 0, 1, 1])
        ax.set_facecolor("#11111b")
        ax.axis("off")  # remove axes
        ax.text(
            0.5,
            0.5,
            f"${latex}$",
            color="#cdd6f4",
            fontsize=20,
            ha="center",
            va="center",
        )
        temp_path = "image/temp/latex.png"
        plt.savefig(
            temp_path, facecolor="#11111b", transparent=False
        )  # save temporary image
        plt.close(fig)
        await ctx.send(file=discord.File(temp_path))  # Send the image

    @commands.hybrid_command("mgraph")
    async def graphcalc(self, ctx, *, equation: str):
        """Graph mathematical equations (separate multiple equations with \";\")"""
        equations = equation.split(";")

        plt.figure(figsize=(10, 6), facecolor="#11111b")
        ax = plt.gca()
        ax.spines["left"].set_position("zero")
        ax.spines["bottom"].set_position("zero")
        ax.spines["right"].set_color("#cdd6f4")
        ax.spines["top"].set_color("#cdd6f4")
        ax.tick_params(axis="x", colors="#cdd6f4")
        ax.tick_params(axis="y", colors="#cdd6f4")
        ax.spines["left"].set_color("#cdd6f4")
        ax.spines["bottom"].set_color("#cdd6f4")
        plt.rcParams["axes.facecolor"] = "#11111b"
        plt.rcParams["figure.facecolor"] = "#11111b"
        plt.rcParams["text.color"] = "#cdd6f4"
        plt.rcParams["axes.labelcolor"] = "#cdd6f4"
        plt.rcParams["xtick.color"] = "#cdd6f4"
        plt.rcParams["ytick.color"] = "#cdd6f4"
        plt.rcParams["axes.edgecolor"] = "#cdd6f4"
        plt.rcParams["grid.color"] = "#cdd6f4"
        plt.rcParams["legend.facecolor"] = "#11111b"
        plt.rcParams["legend.edgecolor"] = "#cdd6f4"
        plt.rcParams["legend.labelcolor"] = "#cdd6f4"
        plt.rcParams["savefig.facecolor"] = "#11111b"

        x = np.linspace(-10, 10, 50)

        for eq in equations:
            eq = eq.strip()
            try:
                # Replace common mathematical notations
                eq = eq.replace("^", "**")
                eq = eq.replace("sin", "np.sin")
                eq = eq.replace("cos", "np.cos")
                eq = eq.replace("tan", "np.tan")
                eq = eq.replace("exp", "np.exp")
                eq = eq.replace("log", "np.log")
                eq = eq.replace("sqrt", "np.sqrt")
                eq = eq.replace("pi", "np.pi")

                # Evaluate the equation
                y = eval(f"lambda x: {eq}")(x)
                plt.plot(x, y, label=eq)

            except Exception as e:
                await ctx.send(f"Error plotting equation '{eq}': {str(e)}")
                return

        plt.grid(True, alpha=0.3)
        plt.legend()
        # Save and send the plot
        temp_path = "image/temp/graph.png"
        plt.savefig(temp_path, bbox_inches="tight", pad_inches=0)
        plt.close()

        await ctx.send(file=discord.File(temp_path))

    @commands.hybrid_command(name="dgraph")
    async def graphdata(
        self, ctx, *, data: str, title="Data Visualization", xlabel="X", ylabel="Y"
    ):
        """Plot multiple data series (format: title1: y1 y2 y3; title2: y1 y2 y3;...)"""
        try:
            # Parse the input data
            series = data.split(";")
            plt.figure(figsize=(10, 6))

            # Set dark mode colors
            plt.rcParams["axes.facecolor"] = "#11111b"
            plt.rcParams["figure.facecolor"] = "#11111b"
            plt.rcParams["text.color"] = "#cdd6f4"
            plt.rcParams["axes.labelcolor"] = "#cdd6f4"
            plt.rcParams["xtick.color"] = "#cdd6f4"
            plt.rcParams["ytick.color"] = "#cdd6f4"
            plt.rcParams["axes.edgecolor"] = "#cdd6f4"
            plt.rcParams["grid.color"] = "#cdd6f4"
            plt.rcParams["legend.facecolor"] = "#11111b"
            plt.rcParams["legend.edgecolor"] = "#cdd6f4"
            plt.rcParams["legend.labelcolor"] = "#cdd6f4"
            plt.rcParams["savefig.facecolor"] = "#11111b"

            for i, serie in enumerate(series):
                if not serie.strip():
                    continue

                # Split title and points
                title2, points_str = serie.split(":")
                title2 = title2.strip()

                # Parse y values and create x indices
                y_values = [float(y) for y in points_str.split()]
                x_values = list(range(len(y_values)))

                # Plot with different colors for each series
                plt.plot(x_values, y_values, "o-", label=title2)

                # Add points labels
                for j, (x, y) in enumerate(zip(x_values, y_values)):
                    plt.annotate("", (x, y), xytext=(5, 5), textcoords="offset points")

            # Customize the plot
            plt.grid(True, alpha=0.3)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.legend()

            # Adjust layout to maximize graph space
            plt.tight_layout()

            # Save and send the plot
            temp_path = "image/temp/dataplot.png"
            plt.savefig(temp_path, bbox_inches="tight", pad_inches=0.1)
            plt.close()

            await ctx.send(file=discord.File(temp_path))

        except Exception as e:
            await ctx.send(
                f"Error plotting data: {str(e)}\nFormat should be: title1: y1 y2 y3; title2: y1 y2 y3;..."
            )

    @commands.hybrid_command()
    async def piechart(self, ctx, *, data: str):
        """Plot a Pie Chart (format: title1, percent; title2, percent)"""
        try:
            # Split the data into pairs
            pairs = [pair.strip() for pair in data.split(";")]

            # Parse labels and values
            labels = []
            values = []

            for pair in pairs:
                if not pair.strip():
                    continue

                label, value = pair.split(",")
                labels.append(label.strip())
                values.append(float(value.strip()))

            # Create figure with dark theme
            plt.figure(figsize=(10, 8))
            plt.rcParams["text.color"] = "#cdd6f4"
            plt.rcParams["axes.labelcolor"] = "#cdd6f4"
            plt.rcParams["xtick.color"] = "#cdd6f4"
            plt.rcParams["ytick.color"] = "#cdd6f4"
            plt.rcParams["axes.edgecolor"] = "#cdd6f4"
            plt.rcParams["legend.facecolor"] = "#11111b"
            plt.rcParams["legend.edgecolor"] = "#cdd6f4"
            plt.rcParams["legend.labelcolor"] = "#cdd6f4"
            plt.rcParams["savefig.facecolor"] = "#11111b"

            # Create pie chart
            wedges,texts,autotexts = plt.pie(values, labels=None, autopct="", startangle=90)
            plt.axis("equal")
            legend_labels = [f'{label}\n({perc:.1f}%)' for label, perc in zip(labels, values)]
            plt.legend(wedges, legend_labels)

            # Save and send the plot
            temp_path = "image/temp/piechart.png"
            plt.savefig(temp_path, bbox_inches="tight", pad_inches=0.1)
            plt.close()

            await ctx.send(file=discord.File(temp_path))
        except Exception as e:
            await ctx.send(
                f"Error creating pie chart: {str(e)}\nFormat should be: title1, percent; title2, percent;..."
            )


async def setup(bot):
    await bot.add_cog(Calculations(bot))
