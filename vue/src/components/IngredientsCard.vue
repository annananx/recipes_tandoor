<template>
    <div class="ingredients" :class="{ 'card border-primary no-border': header }">
        <div :class="{ 'card-body': header, 'p-0': header }">
            <div class="card-header" v-if="header">
                <div class="row">
                    <div class="col-6">
                        <h4 class="card-title"><i class="fas fa-pepper-hot"></i> {{ $t("Ingredients") }}</h4>
                    </div>
                </div>
            </div>
            <div class="card-body">

                <div class="row no-gutter">
                    <div class="col-12 m-0" :class="{ 'p-0': !header }">
                        <table class="table table-sm mb-0">
                            <!-- eslint-disable vue/no-v-for-template-key-on-child -->
                            <template v-for="s in steps">
                                <template v-for="i in s.ingredients">
                                    <ingredient-component
                                        :ingredient="i"
                                        :ingredient_factor="ingredient_factor"
                                        :key="i.id"
                                        :detailed="detailed"
                                        @checked-state-changed="$emit('checked-state-changed', $event)"
                                    />
                                </template>
                            </template>
                            <!-- eslint-enable vue/no-v-for-template-key-on-child -->
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from "vue"
import {BootstrapVue} from "bootstrap-vue"
import "bootstrap-vue/dist/bootstrap-vue.css"

import IngredientComponent from "@/components/IngredientComponent"
import {ApiMixin} from "@/utils/utils"

Vue.use(BootstrapVue)

export default {
    name: "IngredientCard",
    mixins: [ApiMixin],
    components: {IngredientComponent},
    props: {
        steps: {
            type: Array,
            default() {
                return []
            },
        },
        recipe: {type: Number},
        ingredient_factor: {type: Number, default: 1},
        servings: {type: Number, default: 1},
        detailed: {type: Boolean, default: true},
        header: {type: Boolean, default: false},
        recipe_list: {type: Number, default: undefined},
    },
    data() {
        return {

        }
    },
    computed: {

    },
    watch: {

    },
    mounted() {

    },
    methods: {

    },
}
</script>
