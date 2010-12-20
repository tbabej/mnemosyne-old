#
# tag_tree.py <Peter.Bienstman@UGent.be>
#

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.libmnemosyne.component import Component
from mnemosyne.libmnemosyne.utils import numeric_string_cmp


class TagTree(Component, dict):

    """Organises the tags in a hierarchical tree. By convention, hierarchical
    levels in tags are denoted by a :: separator.

    This class is not meant to be instantiated at run time, but rather only
    when it is needed.

    The internal tree datastructure for e.g. the two tags A::B::C and A::B::D
    looks as follows:
    
    self[_("__ALL__")] = ["A"]
    self["A"] = ["A::B"]
    self["A::B"] = ["A::B::C", "A::B::D"]

    Each tree level stores the entire partial tag (i.e. A::B instead of B) to
    guarantee uniqueness.

    Apart from the dictionary in self, this class also contains
    self.display_name_for_node and self.card_count_for_node, with node being
    the index field for the main dictionary self.

    """
    
    def __init__(self, component_manager):
        Component.__init__(self, component_manager)
        self["__ALL__"] = []
        self.display_name_for_node = {"__ALL__": _("All tags")}
        self.card_count_for_node = {}
        tag_names = sorted([tag.name for tag in self.database().tags()],
            cmp=numeric_string_cmp)
        for tag_name in tag_names:
            self.card_count_for_node[tag_name] = \
                self.database().total_card_count_for_tag\
                (self.database().get_or_create_tag_with_name(tag_name))
            if tag_name == "__UNTAGGED__":
                continue  # Add it at the very end for esthetical reasons.
            parent = "__ALL__"
            partial_tag = ""
            levels = tag_name.split("::")
            for node in tag_name.split("::"):
                if partial_tag:
                    partial_tag += "::"
                partial_tag += node
                if not partial_tag in self.display_name_for_node:
                    self[parent].append(partial_tag)
                    self[partial_tag] = []
                    self.display_name_for_node[partial_tag] = node 
                parent = partial_tag
        if "__UNTAGGED__" in tag_names:
            self["__ALL__"].append("__UNTAGGED__")
            self.display_name_for_node["__UNTAGGED__"] = _("Untagged")
            self["__UNTAGGED__"] = []
        self._determine_card_count("__ALL__")

    def _determine_card_count(self, node):
        count = 0
        # If an internal node is a full tag too (e.g. when you have both tags
        # 'A' and 'A::B', be sure to count the upper level too.
        if node in self.card_count_for_node:
            count += self.card_count_for_node[node]
        # Count sublevels.
        for subnode in self[node]:
            count += self._determine_card_count(subnode)
        self.card_count_for_node[node] = count
        return self.card_count_for_node[node]
