new Vue({
    el: '#app',
    data: {
        message: "",
    },
    watch: {},
    async mounted() {
        const resp = await axios.get("/api/sample");
        this.message = resp.data;
    },
    methods: {}
});
