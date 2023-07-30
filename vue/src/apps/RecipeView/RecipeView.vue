<template>
    <div id="app" class="recipe" v-if="recipe_id !== undefined">
        <recipe-view-component :recipe_id="recipe_id"></recipe-view-component>
    </div>
</template>

<script>
import Vue from "vue"
import {BootstrapVue} from "bootstrap-vue"
import "bootstrap-vue/dist/bootstrap-vue.css"

import RecipeViewComponent from "@/components/RecipeViewComponent.vue";

Vue.use(BootstrapVue)

export default {
    name: "RecipeView",
    mixins: [],
    components: {
        RecipeViewComponent,
    },
    computed: {},
    data() {
        return {
            recipe_id: window.RECIPE_ID
        }
    },
    mounted() {
        this.$i18n.locale = window.CUSTOM_LOCALE
    },
    methods: {},
}
</script>

<style>

</style>
