"""Manifest and texture configuration file handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

def write_player_animation(animations_dir: Path) -> None:
    """
    Write the Geyser custom disable animation file.

    This animation is used to disable model rendering when needed.

    Args:
        animations_dir: Directory where the animation file should be written.

    Returns:
        None. Creates the animation file.
    """
    animations_dir.mkdir(parents=True, exist_ok=True)
    
    payload = {"format_version": "1.10.0", "animation_controllers": {"controller.animation.player.crossbow": {"initial_state": "default", "states": {"charge": {"animations": ["third_person_crossbow_equipped"], "transitions": [{"default": "!query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:crossbow') || (!query.is_using_item && query.item_remaining_use_duration <= 0.0 && !query.item_is_charged)"}, {"hold": "query.item_is_charged"}]}, "default": {"transitions": [{"hold": "query.item_is_charged"}, {"charge": "query.is_using_item && query.item_remaining_use_duration > 0.0 && !query.item_is_charged"}]}, "hold": {"animations": ["crossbow_hold"], "transitions": [{"default": "!query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:crossbow') || (!query.is_using_item && query.item_remaining_use_duration <= 0.0 && !query.item_is_charged)"}, {"charge": "query.is_using_item && query.item_remaining_use_duration > 0.0 && !query.item_is_charged"}]}}}, "controller.animation.player.root": {"initial_state": "first_person", "states": {"first_person": {"animations": [{"first_person_swap_item": "!query.blocking"}, {"first_person_shield_block": "query.blocking"}, {"first_person_attack_controller": "variable.attack_time > 0.0f && query.get_equipped_item_name != 'filled_map'"}, "first_person_base_pose", {"first_person_empty_hand": "query.get_equipped_item_name(0, 1) != 'filled_map'"}, {"first_person_walk": "variable.bob_animation"}, {"first_person_map_controller": "(query.get_equipped_item_name(0, 1) == 'filled_map' || query.get_equipped_item_name('off_hand') == 'filled_map')"}, {"first_person_crossbow_equipped": "query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:crossbow') && (variable.item_use_normalized > 0 && variable.item_use_normalized < 1.0)"}, {"first_person_breathing_bob": "variable.attack_time <= 0.0"}], "transitions": [{"paperdoll": "variable.is_paperdoll"}, {"map_player": "variable.map_face_icon"}, {"third_person": "!variable.is_first_person"}]}, "map_player": {"transitions": [{"paperdoll": "variable.is_paperdoll"}, {"first_person": "variable.is_first_person"}, {"third_person": "!variable.map_face_icon && !variable.is_first_person"}]}, "paperdoll": {"animations": ["humanoid_base_pose", "look_at_target_ui", "move.arms", "move.legs", "cape"], "transitions": [{"first_person": "!variable.is_paperdoll && variable.is_first_person"}, {"map_player": "variable.map_face_icon"}, {"third_person": "!variable.is_paperdoll && !variable.is_first_person"}]}, "third_person": {"animations": ["humanoid_base_pose", {"look_at_target": "!query.is_sleeping && !query.is_emoting"}, "move.arms", "move.legs", "cape", {"riding.arms": "query.is_riding"}, {"riding.legs": "query.is_riding"}, "holding", {"brandish_spear": "variable.is_brandishing_spear"}, {"holding_spyglass": "variable.is_holding_spyglass"}, {"charging": "query.is_charging"}, {"sneaking": "query.is_sneaking && !query.is_sleeping"}, {"bob": "!variable.is_holding_spyglass && !variable.is_tooting_goat_horn"}, {"damage_nearby_mobs": "variable.damage_nearby_mobs"}, {"swimming": "variable.swim_amount > 0.0"}, {"swimming.legs": "variable.swim_amount > 0.0"}, {"use_item_progress": "( variable.use_item_interval_progress > 0.0 ) || ( variable.use_item_startup_progress > 0.0 ) && !variable.is_brandishing_spear && !variable.is_holding_spyglass && !variable.is_tooting_goat_horn && !query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:bow')"}, {"sleeping": "query.is_sleeping && query.is_alive"}, {"attack.positions": "variable.attack_time >= 0.0"}, {"attack.rotations": "variable.attack_time >= 0.0"}, {"shield_block_main_hand": "query.blocking && query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:shield')"}, {"shield_block_off_hand": "query.blocking && query.is_item_name_any('slot.weapon.offhand', 0, 'minecraft:shield')"}, {"crossbow_controller": "query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:crossbow')"}, {"third_person_bow_equipped": "query.is_item_name_any('slot.weapon.mainhand', 0, 'minecraft:bow') && (q.is_using_item)"}, {"tooting_goat_horn": "variable.is_tooting_goat_horn"}], "transitions": [{"paperdoll": "variable.is_paperdoll"}, {"first_person": "variable.is_first_person"}, {"map_player": "variable.map_face_icon"}]}}}}}
    
    (animations_dir / "player_custom.animation_controllers.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

def write_disable_animation(animations_dir: Path) -> None:
    """
    Write the Geyser custom disable animation file.

    This animation is used to disable model rendering when needed.

    Args:
        animations_dir: Directory where the animation file should be written.

    Returns:
        None. Creates the animation file.
    """
    animations_dir.mkdir(parents=True, exist_ok=True)
    
    payload = {
        "format_version": "1.8.0",
        "animations": {
            "animation.geyser_custom.disable": {
                "loop": True,
                "override_previous_animation": True,
                "bones": {"geyser_custom": {"scale": 0}},
            }
        },
    }
    
    (animations_dir / "animation.geyser_custom.disable.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    payload = {"format_version": "1.8.0", "animations": {"animation.player.first_person.attack_rotation": {"loop": True, "bones": {"rightarm": {"position": ["math.clamp(-15.5 * math.sin(variable.first_person_rotation_factor * variable.attack_time * 112.0), -7.0, 999.0) * math.sin(variable.first_person_rotation_factor * variable.attack_time * 112.0)", "math.sin(variable.first_person_rotation_factor * (1.0 - variable.attack_time) * (1.0 - variable.attack_time) * 200.0) * 7.5 - variable.first_person_rotation_factor * variable.attack_time * 15.0 + variable.short_arm_offset_right", "math.sin(variable.first_person_rotation_factor * variable.attack_time * 120.0) * 1.75"], "rotation": ["math.sin(variable.first_person_rotation_factor * (1.0 - variable.attack_time) * (1.0 - variable.attack_time) * 280.0) * (query.equipped_item_is_attachable('main_hand') ? -30.0 : -60.0)", "math.sin(variable.first_person_rotation_factor * (1.0 - variable.attack_time) * (1.0 - variable.attack_time) * 280.0) * (query.equipped_item_is_attachable('main_hand') ?  75.0 :  40.0)", "math.sin(variable.first_person_rotation_factor * (1.0 - variable.attack_time) * (1.0 - variable.attack_time) * 280.0) * (query.equipped_item_is_attachable('main_hand') ? -25.0 :  20.0)"]}}}, "animation.player.first_person.vr_attack_rotation": {"loop": True, "bones": {"rightarm": {"position": ["5.0 * math.sin(variable.first_person_rotation_factor * variable.attack_time * 112.0)", "(math.sin(variable.first_person_rotation_factor * (1.0 - variable.attack_time) * (1.0 - variable.attack_time) * 200.0) - 0.8) * 8.75 + 5.0", "math.sin(variable.first_person_rotation_factor * variable.attack_time * 120.0) * 15.0"], "rotation": ["30.7 * math.sin(variable.first_person_rotation_factor * variable.attack_time * -180.0 - 45.0) * 1.5", 0.0, "21.8 * math.sin(variable.first_person_rotation_factor * variable.attack_time * 200.0 + 30.0) * 1.25"]}}}}}

        
    (animations_dir / "player_firstperson.geyser.animation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

def write_texture_manifest(
    path: Path, 
    atlas_name: str, 
    texture_data: Mapping[str, Any]
) -> None:
    """
    Write a Bedrock texture manifest file.

    Args:
        path: Destination path for the manifest file.
        atlas_name: Name of the texture atlas (e.g., "atlas.items").
        texture_data: Mapping of texture identifiers to their configuration.

    Returns:
        None. Writes the manifest file.
    """
    payload = {
        "resource_pack_name": "geyser_custom",
        "texture_name": atlas_name,
        "texture_data": texture_data,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

def write_entity_data(
    path: Path, 
) -> None:
    """
    Write a Bedrock texture manifest file.

    Args:
        path: Destination path for the manifest file.
        atlas_name: Name of the texture atlas (e.g., "atlas.items").
        texture_data: Mapping of texture identifiers to their configuration.

    Returns:
        None. Writes the manifest file.
    """
    
    payload = {"materials": {"version": "1.0.0", "entity_alphatest_one_sided_glint:entity_alphablend": {"+defines": ["GLINT"]}}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
