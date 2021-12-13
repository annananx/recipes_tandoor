import json
from datetime import timedelta

import factory
import pytest
from django.contrib import auth
from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django_scopes import scopes_disabled
from pytest_factoryboy import LazyFixture, register

from cookbook.models import Ingredient, ShoppingListEntry
from cookbook.tests.factories import MealPlanFactory, RecipeFactory, UserFactory

SHOPPING_LIST_URL = 'api:shoppinglistentry-list'
SHOPPING_RECIPE_URL = 'api:recipe-shopping'


@pytest.fixture()
def user2(request, u1_s1):
    try:
        params = request.param  # request.param is a magic variable
    except AttributeError:
        params = {}
    user = auth.get_user(u1_s1)
    user.userpreference.mealplan_autoadd_shopping = True
    user.userpreference.mealplan_autoinclude_related = True
    key = list(params)[0]
    setattr(user.userpreference, key, params[key])
    user.userpreference.save
    return u1_s1


@pytest.fixture()
def recipe(request, space_1, u1_s1):
    try:
        params = request.param  # request.param is a magic variable
    except AttributeError:
        params = {}
    step_recipe = params.get('steps__count', 1)
    steps__recipe_count = params.get('steps__recipe_count', 0)
    steps__food_recipe_count = params.get('steps__food_recipe_count', {})
    created_by = params.get('created_by', auth.get_user(u1_s1))

    return RecipeFactory.create(
        steps__recipe_count=steps__recipe_count,
        steps__food_recipe_count=steps__food_recipe_count,
        created_by=created_by,
        space=space_1,
    )


@pytest.mark.parametrize("arg", [
    ['g1_s1', 204],
    ['u1_s1', 204],
    ['u1_s2', 404],
    ['a1_s1', 204],
])
@pytest.mark.parametrize("recipe, sle_count", [
    ({}, 10),
    ({'steps__recipe_count': 1}, 20),  # shopping list from recipe with StepRecipe
    ({'steps__food_recipe_count': {'step': 0, 'count': 1}}, 19),  # shopping list from recipe with food recipe
    ({'steps__food_recipe_count': {'step': 0, 'count': 1}, 'steps__recipe_count': 1}, 29),  # shopping list from recipe with StepRecipe and food recipe
], indirect=['recipe'])
def test_shopping_recipe_method(request, arg, recipe, sle_count,  u1_s1, u2_s1):
    c = request.getfixturevalue(arg[0])
    user = auth.get_user(c)
    user.userpreference.mealplan_autoadd_shopping = True
    user.userpreference.save()

    assert len(json.loads(c.get(reverse(SHOPPING_LIST_URL)).content)) == 0

    url = reverse(SHOPPING_RECIPE_URL, args={recipe.id})
    r = c.put(url)
    assert r.status_code == arg[1]
    # only PUT method should work
    if r.status_code == 204:  # skip anonymous user

        r = json.loads(c.get(reverse(SHOPPING_LIST_URL)).content)
        assert len(r) == sle_count  # recipe factory creates 10 ingredients by default
        assert [x['created_by']['id'] for x in r].count(user.id) == sle_count
        # user in space can't see shopping list
        assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == 0
        user.userpreference.shopping_share.add(auth.get_user(u2_s1))
        # after share, user in space can see shopping list
        assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == sle_count
        # confirm that the author of the recipe doesn't have access to shopping list
        if c != u1_s1:
            assert len(json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)) == 0

        r = c.get(url)
        assert r.status_code == 405
        r = c.post(url)
        assert r.status_code == 405
        r = c.delete(url)
        assert r.status_code == 405


@pytest.mark.parametrize("recipe, sle_count", [
    ({}, 10),
    ({'steps__recipe_count': 1}, 20),  # shopping list from recipe with StepRecipe
    ({'steps__food_recipe_count': {'step': 0, 'count': 1}}, 19),  # shopping list from recipe with food recipe
    ({'steps__food_recipe_count': {'step': 0, 'count': 1}, 'steps__recipe_count': 1}, 29),  # shopping list from recipe with StepRecipe and food recipe
], indirect=['recipe'])
@pytest.mark.parametrize("use_mealplan", [(False), (True), ])
def test_shopping_recipe_edit(request, recipe, sle_count, use_mealplan, u1_s1, u2_s1):
    # tests editing shopping list via recipe or mealplan
    user = auth.get_user(u1_s1)
    user2 = auth.get_user(u2_s1)
    user.userpreference.mealplan_autoinclude_related = True
    user.userpreference.mealplan_autoadd_shopping = True
    user.userpreference.shopping_share.add(user2)
    user.userpreference.save()

    if use_mealplan:
        mealplan = MealPlanFactory(space=recipe.space, created_by=user, servings=recipe.servings, recipe=recipe)
    else:
        u1_s1.put(reverse(SHOPPING_RECIPE_URL, args={recipe.id}))
    r = json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)
    assert [x['created_by']['id'] for x in r].count(user.id) == sle_count
    all_ing = [x['ingredient'] for x in r]
    keep_ing = all_ing[1:-1]  # remove first and last element
    del keep_ing[int(len(keep_ing)/2)]  # remove a middle element
    list_recipe = r[0]['list_recipe']
    amount_sum = sum([x['amount'] for x in r])

    # test modifying shopping list as different user
    # test increasing servings size of recipe shopping list
    if use_mealplan:
        mealplan.servings = 2*recipe.servings
        mealplan.save()
    else:
        u2_s1.put(reverse(SHOPPING_RECIPE_URL, args={recipe.id}),
                  {'list_recipe': list_recipe, 'servings': 2*recipe.servings},
                  content_type='application/json'
                  )
    r = json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)
    assert sum([x['amount'] for x in r]) == amount_sum * 2
    assert len(r) == sle_count
    assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == sle_count

    # testing decreasing servings size of recipe shopping list
    if use_mealplan:
        mealplan.servings = .5 * recipe.servings
        mealplan.save()
    else:
        u1_s1.put(reverse(SHOPPING_RECIPE_URL, args={recipe.id}),
                  {'list_recipe': list_recipe, 'servings': .5 * recipe.servings},
                  content_type='application/json'
                  )
    r = json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)
    assert sum([x['amount'] for x in r]) == amount_sum * .5
    assert len(r) == sle_count
    assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == sle_count

    # test removing 2 items from shopping list
    u2_s1.put(reverse(SHOPPING_RECIPE_URL, args={recipe.id}),
              {'list_recipe': list_recipe, 'ingredients': keep_ing},
              content_type='application/json'
              )
    r = json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)
    assert len(r) == sle_count - 3
    assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == sle_count - 3

    # add all ingredients to existing shopping list - don't change serving size
    u2_s1.put(reverse(SHOPPING_RECIPE_URL, args={recipe.id}),
              {'list_recipe': list_recipe, 'ingredients': all_ing},
              content_type='application/json'
              )
    r = json.loads(u1_s1.get(reverse(SHOPPING_LIST_URL)).content)
    assert sum([x['amount'] for x in r]) == amount_sum * .5
    assert len(r) == sle_count
    assert len(json.loads(u2_s1.get(reverse(SHOPPING_LIST_URL)).content)) == sle_count


# auto add shopping, no
# auto include related, no
# auto ignore onhand
# ignore shopping food
@pytest.mark.parametrize("user2, sle_count", [
    ({'mealplan_autoadd_shopping': False}, 0),
    ({'mealplan_autoinclude_related': False}, 9),
    ({'mealplan_autoexclude_onhand': True}, 27),  # shopping list from recipe with StepRecipe
], indirect=['user2'])
@pytest.mark.parametrize("use_mealplan", [(False), (True), ])
@pytest.mark.parametrize("recipe", [({'steps__recipe_count': 1})], indirect=['recipe'])
def test_shopping_recipe_userpreference(request, recipe, sle_count, use_mealplan, user2):
    with scopes_disabled():
        user = auth.get_user(user2)
        # setup recipe with 10 ingredients, 1 step recipe with 10 ingredients, 1 food onhand, 1 food ignore shopping
        recipe.step.all()


def test_shopping_recipe_mixed_authors(request, user2):
    assert 1 == 1


# TODO test creating shopping list from recipe that includes recipes from multiple users
# TODO meal plan recipe with all the user preferences tested
