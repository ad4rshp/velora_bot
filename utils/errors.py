"""
Global Error Handling Infrastructure for Velora.
Catches, logs, and formats exceptions into friendly user responses.
"""

import discord
from discord.ext import commands
import traceback
from utils.logger import error_logger
from utils.embeds import Embeds

class VeloraException(Exception):
    """Base exception for application-level RPG logic errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class InsufficientFundsError(VeloraException):
    """Raised when a player lacks necessary coins or sigils."""
    pass

class ItemNotFoundError(VeloraException):
    """Raised when an item/character/scroll is not found."""
    pass

async def global_on_command_error(ctx: commands.Context, error: Exception) -> None:
    """Global command error handler filtering internal tracebacks from end-users."""
    
    # Unwrap CommandInvokeError
    if isinstance(error, commands.CommandInvokeError):
        error = error.original

    # Application custom errors
    if isinstance(error, VeloraException):
        await ctx.send(embed=Embeds.error("Action Failed", error.message))
        return

    # Cooldown errors
    if isinstance(error, commands.CommandOnCooldown):
        retry = f"{error.retry_after:.1f}"
        await ctx.send(embed=Embeds.warning("Cooldown Active", f"Please wait `{retry}s` before using this command again."))
        return

    # Missing Permissions
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=Embeds.error("Permission Denied", "You do not have permission to execute this command."))
        return

    # Not Owner
    if isinstance(error, commands.NotOwner):
        await ctx.send(embed=Embeds.error("Access Restricted", "This command is restricted to bot developers."))
        return

    # Command Not Found (silently ignore or subtle message)
    if isinstance(error, commands.CommandNotFound):
        return

    # User Input Validation / Parsing Errors
    if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
        await ctx.send(embed=Embeds.warning("Invalid Usage", f"{str(error).capitalize()}\nCheck `{ctx.prefix}help` for usage details."))
        return

    # Unexpected internal exception (Log real error, show clean message)
    tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    error_logger.error(
        f"Unhandled Command Exception in '{ctx.command}' invoked by {ctx.author} ({ctx.author.id}):\n{tb_text}"
    )

    await ctx.send(
        embed=Embeds.error("Error", "That action couldn't be completed. If this persists, please notify support.")
    )
