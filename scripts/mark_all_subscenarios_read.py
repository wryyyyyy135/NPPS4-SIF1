"""
Script to mark all subscenarios (side stories) as read.
Optionally grants rewards (1 loveca + 20000 coins per subscenario) for unread ones.

This modifies user data (not backend data), so it's safe to use.
"""

import argparse

import sqlalchemy

import npps4.idol
import npps4.system.subscenario
import npps4.system.advanced
import npps4.system.item
import npps4.const
import npps4.db.main
import npps4.db.subscenario
import npps4.scriptutils.user


async def run_script(arg: list[str]):
    parser = argparse.ArgumentParser(
        description="Mark all subscenarios as read. Optionally grant rewards for unread ones."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    npps4.scriptutils.user.register_args(group)
    parser.add_argument(
        "--with-rewards",
        action="store_true",
        help="Grant rewards (1 loveca + 20000 coins) for subscenarios that weren't already completed.",
    )
    parser.add_argument(
        "--unread",
        action="store_true",
        help="Mark as unread instead of read (opposite of default behavior).",
    )
    args = parser.parse_args(arg)

    async with npps4.idol.BasicSchoolIdolContext(lang=npps4.idol.Language.en) as context:
        target_user = await npps4.scriptutils.user.from_args(context, args)
        
        # Get all available subscenarios from the game database
        q = sqlalchemy.select(npps4.db.subscenario.SubScenario)
        result = await context.db.subscenario.execute(q)
        all_subscenarios = list(result.scalars())
        
        total_count = 0
        newly_completed = 0
        already_completed = 0
        rewards_granted = 0
        
        print(f"Processing {len(all_subscenarios)} subscenarios...")
        
        for game_subsc in all_subscenarios:
            # Get or create user's subscenario entry
            subsc = await npps4.system.subscenario.get(context, target_user, game_subsc.subscenario_id)
            was_already_completed = False
            
            if subsc is None:
                # Unlock it first
                subsc = npps4.db.main.SubScenario(
                    user_id=target_user.id,
                    subscenario_id=game_subsc.subscenario_id,
                    completed=False,
                )
                context.db.main.add(subsc)
            else:
                was_already_completed = subsc.completed
            
            # Mark as read/unread
            should_be_completed = not args.unread
            if subsc.completed != should_be_completed:
                subsc.completed = should_be_completed
                if should_be_completed and not was_already_completed:
                    newly_completed += 1
                    
                    # Grant rewards if requested and this is being marked as completed
                    if args.with_rewards:
                        # Add loveca
                        loveca_item = npps4.system.item.loveca(npps4.const.SUBSCENARIO_LOVECA_REWARD_AMOUNT)
                        loveca_item.comment = npps4.const.SUBSCENARIO_REWARD_COMMENT_EN
                        await npps4.system.advanced.add_item(context, target_user, loveca_item)
                        
                        # Add game coins
                        coin_item = npps4.system.item.game_coin(npps4.const.SUBSCENARIO_GAME_COIN_REWARD_AMOUNT)
                        await npps4.system.advanced.add_item(context, target_user, coin_item)
                        
                        rewards_granted += 1
                elif was_already_completed:
                    already_completed += 1
            
            total_count += 1
        
        # Commit all changes
        await context.db.main.flush()
        
        print(f"\n✓ Completed processing {total_count} subscenarios")
        if not args.unread:
            print(f"  - Newly marked as read: {newly_completed}")
            print(f"  - Already completed: {already_completed}")
            if args.with_rewards:
                print(f"  - Rewards granted: {rewards_granted} subscenarios")
                print(f"    (Total: {rewards_granted} loveca + {rewards_granted * 20000:,} coins)")
        else:
            print(f"  - Marked as unread: {total_count}")


if __name__ == "__main__":
    import npps4.scriptutils.boot

    npps4.scriptutils.boot.start(run_script)

