<template>
    <div>
        <div class="dropdown d-print-none">
            <a class="btn shadow-none pr-0 pl-0" href="javascript:void(0);" role="button" id="dropdownMenuLink" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <i class="fas fa-ellipsis-v fa-lg"></i>
            </a>

            <div class="dropdown-menu dropdown-menu-right" aria-labelledby="dropdownMenuLink">
                <a class="dropdown-item" :href="resolveDjangoUrl('edit_recipe', recipe.id)" v-if="!disabled_options.edit"
                    ><i class="fas fa-pencil-alt fa-fw"></i> {{ $t("Edit") }}</a
                >

                <a class="dropdown-item" v-if="recipe.internal && !disabled_options.shopping" @click="addToShopping" href="#">
                    <i class="fas fa-shopping-cart fa-fw"></i> {{ $t("Add_to_Shopping") }}
                </a>
                <a href="javascript:void(0);">
                    <button class="dropdown-item" @click="createShareLink()" v-if="recipe.internal && !disabled_options.share">
                        <i class="fas fa-share-alt fa-fw"></i> {{ $t("Share") }}
                    </button>
                </a>
            </div>
        </div>

        <shopping-modal :recipe="recipe" :servings="servings_value" :modal_id="modal_id" :mealplan="undefined" />

        <b-modal :id="`modal-share-link_${modal_id}`" v-bind:title="$t('Share')" hide-footer>
            <div class="row">
                <div class="col col-md-12">
                    <label v-if="recipe_share_link !== undefined">{{ $t("Public share link") }}</label>
                    <input ref="share_link_ref" class="form-control" v-model="recipe_share_link" />
                    <b-button class="mt-2 mb-3 d-none d-md-inline" variant="secondary" @click="$bvModal.hide(`modal-share-link_${modal_id}`)">{{ $t("Close") }} </b-button>
                    <b-button class="mt-2 mb-3 ml-md-2" variant="primary" @click="copyShareLink()">{{ $t("Copy") }} </b-button>
                    <b-button class="mt-2 mb-3 ml-2 float-right" variant="success" @click="shareIntend()">{{ $t("Share") }} <i class="fa fa-share-alt"></i></b-button>
                </div>
            </div>
        </b-modal>
    </div>
</template>

<script>
import ShoppingModal from "@/components/Modals/ShoppingModal"
import { ApiApiFactory } from "@/utils/openapi/api"
import { makeToast, resolveDjangoUrl, ResolveUrlMixin, StandardToasts } from "@/utils/utils"
import axios from "axios"
import moment from "moment"
import Vue from "vue"

Vue.prototype.moment = moment

export default {
    name: "RecipeContextMenu",
    mixins: [ResolveUrlMixin],
    components: {
        ShoppingModal,
    },
    data() {
        return {
            servings_value: 0,
            isPinned: false,
            recipe_share_link: undefined,
            modal_id: Math.round(Math.random() * 100000),
            options: {
                entryEditing: {
                    date: null,
                    id: -1,
                    meal_type: null,
                    note: "",
                    note_markdown: "",
                    recipe: null,
                    servings: 1,
                    shared: [],
                    title: "",
                    title_placeholder: this.$t("Title"),
                },
            },
            entryEditing: {},
            mealplan: undefined,
        }
    },
    props: {
        recipe: Object,
        servings: {
            type: Number,
            default: -1,
        },
        disabled_options: {
            type: Object,
            default: () => ({ print: true }),
        },
    },
    mounted() {
        this.servings_value = this.servings === -1 ? this.recipe.servings : this.servings

        let pinnedRecipes = JSON.parse(localStorage.getItem("pinned_recipes")) || []
        this.isPinned = pinnedRecipes.some((r) => r.id == this.recipe.id)
    },
    watch: {
        recipe: {
            handler() {},
            deep: true,
        },
        servings: function (newVal) {
            this.servings_value = parseInt(newVal)
        },
    },
    methods: {
        createShareLink: function () {
            console.log("create")
            axios
                .get(resolveDjangoUrl("api_share_link", this.recipe.id))
                .then((result) => {
                    console.log("success")
                    this.$bvModal.show(`modal-share-link_${this.modal_id}`)
                    this.recipe_share_link = result.data.link
                })
                .catch((err) => {
                    console.log("fail")
                    if (err.response.status === 403) {
                        makeToast(this.$t("Share"), this.$t("Sharing is not enabled for this space or your user account."), "danger")
                    }
                })
        },
        copyShareLink: function () {
            let share_input = this.$refs.share_link_ref
            share_input.select()
            document.execCommand("copy")
        },
        shareIntend: function () {
            let shareData = {
                title: this.recipe.name,
                text: `${this.$t("Check out this recipe: ")} ${this.recipe.name}`,
                url: this.recipe_share_link,
            }
            navigator.share(shareData)
        },
        addToShopping() {
            this.$bvModal.show(`shopping_${this.modal_id}`)
        },
    },
}
</script>
