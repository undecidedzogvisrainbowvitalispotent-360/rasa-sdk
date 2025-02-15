import pytest

from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.knowledge_base.actions import ActionQueryKnowledgeBase
from rasa_sdk.knowledge_base.storage import InMemoryKnowledgeBase
from rasa_sdk.knowledge_base.utils import (
    SLOT_MENTION,
    SLOT_ATTRIBUTE,
    SLOT_OBJECT_TYPE,
    SLOT_LISTED_OBJECTS,
    SLOT_LAST_OBJECT,
    SLOT_LAST_OBJECT_TYPE,
)


def compare_slots(slot_list_1, slot_list_2):
    assert len(slot_list_2) == len(slot_list_1)

    for slot_1 in slot_list_1:
        slot_2 = list(filter(lambda x: x["name"] == slot_1["name"], slot_list_2))[0]

        if isinstance(slot_2["value"], list):
            assert set(slot_1["value"]) == set(slot_2["value"])
        else:
            assert slot_1["value"] == slot_2["value"]


@pytest.mark.parametrize(
    "slots,expected_slots",
    [
        (
            {
                SLOT_MENTION: None,
                SLOT_ATTRIBUTE: None,
                SLOT_OBJECT_TYPE: "restaurant",
                SLOT_LISTED_OBJECTS: None,
                SLOT_LAST_OBJECT: None,
                SLOT_LAST_OBJECT_TYPE: None,
            },
            [
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_ATTRIBUTE, None),
                SlotSet(SLOT_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LAST_OBJECT, None),
                SlotSet(SLOT_LAST_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LISTED_OBJECTS, [3, 2, 1]),
            ],
        ),
        (
            {
                SLOT_MENTION: None,
                SLOT_ATTRIBUTE: None,
                SLOT_OBJECT_TYPE: "restaurant",
                SLOT_LISTED_OBJECTS: None,
                SLOT_LAST_OBJECT: None,
                SLOT_LAST_OBJECT_TYPE: "restaurant",
                "cuisine": "Italian",
            },
            [
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_ATTRIBUTE, None),
                SlotSet(SLOT_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LAST_OBJECT, None),
                SlotSet(SLOT_LAST_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LISTED_OBJECTS, [3, 1]),
                SlotSet("cuisine", None),
            ],
        ),
        (
            {
                SLOT_MENTION: "2",
                SLOT_ATTRIBUTE: "cuisine",
                SLOT_OBJECT_TYPE: "restaurant",
                SLOT_LISTED_OBJECTS: [1, 2, 3],
                SLOT_LAST_OBJECT: None,
                SLOT_LAST_OBJECT_TYPE: "restaurant",
            },
            [
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_ATTRIBUTE, None),
                SlotSet(SLOT_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LAST_OBJECT, 2),
                SlotSet(SLOT_LAST_OBJECT_TYPE, "restaurant"),
            ],
        ),
        (
            {
                SLOT_MENTION: None,
                SLOT_ATTRIBUTE: "cuisine",
                SLOT_OBJECT_TYPE: "restaurant",
                SLOT_LISTED_OBJECTS: [1, 2, 3],
                SLOT_LAST_OBJECT: None,
                SLOT_LAST_OBJECT_TYPE: "restaurant",
                "restaurant": "PastaBar",
            },
            [
                SlotSet(SLOT_MENTION, None),
                SlotSet(SLOT_ATTRIBUTE, None),
                SlotSet(SLOT_OBJECT_TYPE, "restaurant"),
                SlotSet(SLOT_LAST_OBJECT, 1),
                SlotSet(SLOT_LAST_OBJECT_TYPE, "restaurant"),
            ],
        ),
        (
            {
                SLOT_MENTION: None,
                SLOT_ATTRIBUTE: None,
                SLOT_OBJECT_TYPE: None,
                SLOT_LISTED_OBJECTS: None,
                SLOT_LAST_OBJECT: None,
                SLOT_LAST_OBJECT_TYPE: None,
            },
            [],
        ),
    ],
)
async def test_action_run(data_file, slots, expected_slots):
    knowledge_base = InMemoryKnowledgeBase(data_file)
    action = ActionQueryKnowledgeBase(knowledge_base)

    dispatcher = CollectingDispatcher()
    tracker = Tracker("default", slots, {}, [], False, None, {}, "action_listen")

    actual_slots = await action.run(dispatcher, tracker, {})

    compare_slots(expected_slots, actual_slots)
    compare_slots(actual_slots, expected_slots)

    # Check that utterances produced by action are correct.
    if slots[SLOT_ATTRIBUTE]:
        if slots.get("restaurant") is not None:

            name = slots["restaurant"]
            attr = slots[SLOT_ATTRIBUTE]
            obj = await knowledge_base.get_object("restaurant", name)
            value = obj[attr]

            expected_msg = f"'{name}' has the value '{value}' for attribute '{attr}'."
            actual_msg = dispatcher.messages[0]["text"]

            assert actual_msg == expected_msg

        elif slots.get(SLOT_MENTION):
            obj = await knowledge_base.get_object("restaurant", slots[SLOT_MENTION])
            name = obj["name"]
            attr = slots[SLOT_ATTRIBUTE]
            value = obj[attr]

            expected_msg = f"'{name}' has the value '{value}' for attribute '{attr}'."
            actual_msg = dispatcher.messages[0]["text"]

            assert actual_msg == expected_msg
