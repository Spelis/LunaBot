import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import numpy as np
import math
import random

class Calculations(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.description = "Math Commands: Graphing, Latex, Evaluation"
        self.emoji = "🧮"
    
    @commands.hybrid_command("latex")
    async def latex(self, ctx, latex: str=""):
        """Render LaTeX"""
        # check if the message contains an attachment (higher priority than the argument)
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            latex = await attachment.read()
            latex = latex.decode('utf-8')
        plt.rcParams['text.usetex'] = self.bot.usetex
        plt.rcParams['text.latex.preamble'] = r'\usepackage{stix}'
        fig = plt.figure(figsize=(4, 1), facecolor='#11111b')
        ax = plt.axes([0, 0, 1, 1])
        ax.set_facecolor('#11111b')
        ax.axis('off') # remove axes
        ax.text(0.5, 0.5, f'${latex}$', color='#cdd6f4', fontsize=20, ha='center', va='center')
        temp_path = 'latex.png'
        plt.savefig(temp_path, facecolor='#11111b', transparent=False) # save temporary image
        plt.close(fig)
        await ctx.send(file=discord.File(temp_path)) # Send the image
        
    @commands.hybrid_command("mgraph")
    async def graphcalc(self, ctx, *, equation: str):
        """Graph mathematical equations (separate multiple equations with \";\")"""
        equations = equation.split(';')
        
        plt.figure(figsize=(10, 6))
        ax = plt.gca()
        ax.spines['left'].set_position('zero')
        ax.spines['bottom'].set_position('zero')
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')
        
        x = np.linspace(-10, 10, 50)
        
        for eq in equations:
            eq = eq.strip()
            try:
                # Replace common mathematical notations
                eq = eq.replace('^', '**')
                eq = eq.replace('sin', 'np.sin')
                eq = eq.replace('cos', 'np.cos')
                eq = eq.replace('tan', 'np.tan')
                eq = eq.replace('exp', 'np.exp')
                eq = eq.replace('log', 'np.log')
                eq = eq.replace('sqrt', 'np.sqrt')
                eq = eq.replace('pi', 'np.pi')
                
                # Evaluate the equation
                y = eval(f"lambda x: {eq}")(x)
                plt.plot(x, y, label=eq)
                
            except Exception as e:
                await ctx.send(f"Error plotting equation '{eq}': {str(e)}")
                return
        
        plt.grid(True, alpha=0.3)
        plt.legend()
        # Save and send the plot
        temp_path = 'graph.png'
        plt.savefig(temp_path)
        plt.close()
        
        await ctx.send(file=discord.File(temp_path))
    
    @commands.hybrid_command(name="dgraph")
    async def graphdata(self, ctx, *, data: str,title = "Data Visualization", xlabel = "X", ylabel = "Y"):
        """Plot multiple data series (format: title1: y1 y2 y3; title2: y1 y2 y3;...)"""
        try:
            # Parse the input data
            series = data.split(';')
            plt.figure(figsize=(10, 6))
            
            for i, serie in enumerate(series):
                if not serie.strip():
                    continue
                    
                # Split title and points
                title, points_str = serie.split(':')
                title = title.strip()
                
                # Parse y values and create x indices
                y_values = [float(y) for y in points_str.split()]
                x_values = list(range(len(y_values)))
                
                # Plot with different colors for each series
                plt.plot(x_values, y_values, 'o-')
                
                # Add points labels
                for j, (x, y) in enumerate(zip(x_values, y_values)):
                    plt.annotate("", (x, y), xytext=(5, 5), textcoords='offset points')
            
            # Customize the plot
            plt.grid(True, alpha=0.3)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.legend()
            
            # Save and send the plot
            temp_path = 'dataplot.png'
            plt.savefig(temp_path)
            plt.close()
            
            await ctx.send(file=discord.File(temp_path))
            
        except Exception as e:
            await ctx.send(f"Error plotting data: {str(e)}\nFormat should be: title1: y1 y2 y3; title2: y1 y2 y3;...")
        
async def setup(bot):
    await bot.add_cog(Calculations(bot))
