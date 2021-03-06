G.datasets = G.datasets.map(function (dataset) {
	dataset.variables = dataset.variables.map(function (variableName) {
		return {
			name: variableName,
			role: "W",
		};
	});
	return dataset;
});

G.models = G.models.map(function (model) {
  model.fields = model.fields.map(function (field) {
    // initialize enum types with empty array so that Vue model
    // works properly
    if (field.type === 'enum') {
      field.value = [];
    } else if (field.default) {
      field.value = field.default;
    }
    return field;
  });

  return model;
})

G.models.unshift({
  name: "Choose an analysis",
  needsDataset: false,
});

function highlightCode () {
 $('pre code').each(function(i, block) {
      hljs.highlightBlock(block);
    });
};

var router = new VueRouter({
    mode: 'history',
    routes: []
});

var app = new Vue({
  router,
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
    message: 'Hello Vue!',
	  modelTemplates: G.models,
	  selectedTemplate: G.models[0],
	  datasets: G.datasets,
	  activeDataset: G.datasets[0],
    ghapCredentials: {
      username: '',
      password: '',
      ip: '',
    },
  },
  mounted: function () {

    var that = this;

    if (this.$route.query.initialChoice) {
      G.models.forEach((model) => {
        if (model.id == this.$route.query.initialChoice) {
          that.selectedTemplate = model;
        }
      });
    }

    highlightCode();
  },
  methods: {
    templateSelected: function (event) {      
      highlightCode();
    },
  	sendJob: function (backend) {
  		var inputs = {};
      inputs.script_params = {}
      this.selectedTemplate.fields.forEach(function (field) {
        inputs.script_params[field.name] = field.value;
      });

  		var whereRole = (variables, role) => {
  			return variables.filter(function (variable) {
  				return variable.role === role;
  			});
  		};

  		var whereRoleForActive = (role) => {
  			var vars = whereRole(this.activeDataset.variables, role);
  			return vars.map(function (variable) {
  				return variable.name;
  			});
  		};

  		inputs.data = {
  			uri: this.activeDataset.url,
  		};

      inputs.nodes = {};
      this.selectedTemplate.roles.forEach(function (role) {
        inputs.nodes[role] = whereRoleForActive(role);
      });

  		var job = {
  			inputs,
        backend,
        ghap_credentials: this.ghapCredentials,
  			model_template: this.selectedTemplate.id,
        dataset: this.activeDataset.id,
  		};

  		// GET /someUrl
  		this.$http.post('/submit_job/', job).then(response => {
  			window.location.href = '/jobs/';
  		}, response => {
  		});

  	},
  },
});



