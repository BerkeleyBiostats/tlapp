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
    }
    return field;
  });
  return model;
})

function highlightCode () {
 $('pre code').each(function(i, block) {
      hljs.highlightBlock(block);
    });
};

var app = new Vue({
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
  	roles: ['W', 'A', 'Y'],
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
    highlightCode();
  },
  methods: {
    templateSelected: function (event) {      
      highlightCode();
    },
  	sendJob: function (backend) {
  		var inputs = {};
      inputs.params = {}
      this.selectedTemplate.fields.forEach(function (field) {
        inputs.params[field.name] = field.value;
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
  			type: 'csv',
  			nodes: {
  				Y: whereRoleForActive('Y'),
  				A: whereRoleForActive('A'),
  				W: whereRoleForActive('W'),
  			}
  		};

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



