"""
Script to unlock every card in the album with max level and max kizuna (bond).

This modifies user data (not backend data), so it's safe to use.
"""

import argparse

import sqlalchemy

import npps4.idol
import npps4.system.album
import npps4.system.unit
import npps4.db.main
import npps4.db.unit
import npps4.scriptutils.user


async def run_script(arg: list[str]):
    parser = argparse.ArgumentParser(
        description="Unlock every card in the album with max level and max kizuna (bond)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    npps4.scriptutils.user.register_args(group)
    args = parser.parse_args(arg)

    async with npps4.idol.BasicSchoolIdolContext(lang=npps4.idol.Language.en) as context:
        target_user = await npps4.scriptutils.user.from_args(context, args)
        
        # Get all units from the game database
        q = sqlalchemy.select(npps4.db.unit.Unit)
        result = await context.db.unit.execute(q)
        all_units = list(result.scalars())
        
        total_count = 0
        newly_unlocked = 0
        already_unlocked = 0
        skipped_support = 0
        
        print(f"Processing {len(all_units)} cards...")
        
        for unit_info in all_units:
            # Skip support cards (they don't have album entries)
            # Support cards typically have disable_rank_up > 0 or are in a different category
            if unit_info.disable_rank_up > 0:
                skipped_support += 1
                continue
            
            # Get rarity info to determine max stats
            rarity = await npps4.system.unit.get_unit_rarity(context, unit_info.rarity)
            if rarity is None:
                print(f"Warning: Could not get rarity for unit_id {unit_info.unit_id}, skipping...")
                continue
            
            # Check if already in album
            has_album = await npps4.system.album.has_ever_got_unit(context, target_user, unit_info.unit_id)
            
            # Determine max love (kizuna) for idolized form (highest possible)
            max_love_idolized = rarity.after_love_max
            
            # Unlock in album with max stats for both idolized and non-idolized forms
            # We set both rank_max (idolized) and rank_level_max (max level) flags
            # And set highest_love to the maximum possible (idolized form)
            await npps4.system.album.update(
                context,
                target_user,
                unit_info.unit_id,
                rank_max=True,  # Idolized form unlocked
                love_max=True,  # Max kizuna reached
                rank_level_max=True,  # Max level reached
                highest_love=max_love_idolized,  # Set to max kizuna (idolized)
                flush=False,  # Batch flush at the end
            )
            
            if not has_album:
                newly_unlocked += 1
            else:
                already_unlocked += 1
            
            total_count += 1
            
            # Progress indicator every 100 cards
            if total_count % 100 == 0:
                print(f"  Processed {total_count} cards...")
        
        # Commit all changes
        await context.db.main.flush()
        
        print(f"\n✓ Completed processing {total_count} cards")
        print(f"  - Newly unlocked in album: {newly_unlocked}")
        print(f"  - Already in album (updated): {already_unlocked}")
        print(f"  - Skipped (support cards): {skipped_support}")
        print(f"\nAll cards are now unlocked in your album with:")
        print(f"  - Max level (both idolized and non-idolized)")
        print(f"  - Max kizuna/bond (both idolized and non-idolized)")


if __name__ == "__main__":
    import npps4.scriptutils.boot

    npps4.scriptutils.boot.start(run_script)

