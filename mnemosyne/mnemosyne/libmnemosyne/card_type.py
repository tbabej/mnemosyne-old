#
# card_type.py <Peter.Bienstman@UGent.be>
#

from mnemosyne.libmnemosyne.card import Card
from mnemosyne.libmnemosyne.utils import CompareOnId
from mnemosyne.libmnemosyne.component import Component


class CardType(Component, CompareOnId):

    """A card type groups a number of fact views on a certain fact, thereby
    forming a set of sister cards.

    A card type needs an id as well as a name, because the name can change
    for different translations.
    
    Inherited card types should have ids where :: separates the different
    levels of the hierarchy, e.g. parent_id::child_id.
    
    The keys from the fact are also given more verbose names here. This is
    not done in fact.py, on one hand to save space in the database, and on
    the other hand to allow the possibility that different card types give
    different names to the same key. (E.g. foreign word' could be called
    'French' in a French card type, or 'pronunciation' could be called
    'reading' in a Kanji card type.) This is done in self.keys_and_names,
    which is a list of the form [(key, key_name)]. It is tempting to use a
    dictionary here, but we can't do that since ordering is important.

    Keys which need to be different for all facts belonging to this card
    type are listed in 'unique_keys'.

    Note that a fact could contain more data than those listed in the card
    type's 'keys_and_names' variable, which could be useful for card types
    needing hidden keys, dynamically generated keys, ... .

    The functions 'create_sister_cards' and 'edit_sister_cards' can be
    overridden by card types which can have a varying number of fact views,
    e.g. the cloze card type.

    """
    
    id = "-1"
    name = ""
    component_type = "card_type"

    keys_and_names = None
    fact_views = None
    unique_keys = None
    required_keys = None
    keyboard_shortcuts = {}
    extra_data = {}

    def keys(self):
        return set(key for (key, key_name) in self.keys_and_names)

    def key_names(self):
        return [key_name for (key, key_name) in self.keys_and_names]
    
    def key_with_name(self, name):
        for key, key_name in self.keys_and_names:
            if key_name == name:
                return key
            
    def render_question(self, card, render_chain="default", **render_args):
        return self.render_chain(render_chain).\
            render_question(card, **render_args)
       
    def render_answer(self, card, render_chain="default", **render_args):
        return self.render_chain(render_chain).\
            render_answer(card, **render_args)

    def is_data_valid(self, data):

        """Check if all the required keys are present."""
        
        for required_key in self.required_keys:
            if required_key not in data or not data[required]:
                return False
        return True
        
    def fact_data(self, card):

        """Returns the data in fact of a card. Normally. this is just
        'card.fact.data', but specialty card types (e.g. the cloze card type)
        can override this.

        """
        
        return card.fact.data

    def create_sister_cards(self, fact):

        """Initial grading of cards and storing in the database should not happen
        here, but is done in the main controller.

        """
        
        return [Card(self, fact, fact_view) for fact_view in self.fact_views]

    def edit_sister_cards(self, fact, new_fact_data):

        """If for the card type this operation results in edited, added or
        deleted card data apart from the edited fact data from which they
        derive, these should be returned here, so that they can be taken into
        account in the database storage.

        Initial grading of cards and storing in the database should not happen
        here, but is done in the main controller.

        """

        new_cards, edited_cards, deleted_cards = [], [], []
        return new_cards, edited_cards, deleted_cards
    
    def key_format_proxies(self):

        """Sometimes, a card type can dynamically create a key when
        generating a question or an answer (see e.g. the cloze card type).
        Since the user cannot specify how this key should be formatted, it
        should be formatted like an other, static key. This function returns
        a dictionary with this correspondence.

        """

        proxies = {}
        for key, key_name in self.keys_and_names:
            proxies[key] = key
        return proxies
