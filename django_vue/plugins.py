from collections import OrderedDict


class VuePlugin:
    vue_script_sources: OrderedDict[str, str] = OrderedDict()
    vue_style_sources: OrderedDict[str, str] = OrderedDict()

    @classmethod
    def get_vue_script_sources(cls):
        return cls.vue_script_sources

    @classmethod
    def get_vue_style_sources(cls):
        return cls.vue_style_sources


class BootstrapVuePlugin(VuePlugin):
    vue_script_sources = OrderedDict(
        [
            ("popperjs", "https://unpkg.com/@popperjs/core@2"),
            ("vue", "https://unpkg.com/vue@latest/dist/vue.min.js"),
            (
                "bootstrap-vue",
                "https://unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue.min.js",
            ),
            (
                "bootstrap-vue-icons",
                "https://unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue-icons.min.js",
            ),
        ]
    )
    vue_style_sources = OrderedDict(
        [
            ("bootstrap", "https://unpkg.com/bootstrap/dist/css/bootstrap.min.css"),
            (
                "bootstrap-vue",
                "https://unpkg.com/bootstrap-vue/dist/bootstrap-vue.min.css",
            ),
        ]
    )


class CompositionAPIPlugin(VuePlugin):
    vue_script_sources = OrderedDict(
        [
            (
                "vue",
                "https://cdn.jsdelivr.net/npm/vue@2.6",
            ),
            (
                "composition-api",
                "https://cdn.jsdelivr.net/npm/@vue/composition-api@1.0.0-beta.20",
            ),
        ]
    )


class VuetifyVuePlugin(VuePlugin):
    vue_script_sources = OrderedDict(
        [
            ("vue", "https://cdn.jsdelivr.net/npm/vue@2.x/dist/vue.js"),
            ("vuetify", "https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.js"),
        ]
    )
    vue_style_sources = OrderedDict(
        [
            (
                "materialdesignicons",
                "https://cdn.jsdelivr.net/npm/@mdi/font@4.x/css/materialdesignicons.min.css",
            ),
            (
                "roboto",
                "https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900",
            ),
            (
                "vuetify",
                "https://cdn.jsdelivr.net/npm/vuetify@2.x/dist/vuetify.min.css",
            ),
        ]
    )
