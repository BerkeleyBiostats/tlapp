var app = new Vue({
  delimiters: ['${', '}'],
  el: '#modelmaker',
  data: {
    message: 'Hello Vue!',
	variables: [
		{
			name: "studyid",
			role: "W",
			isW: true,
		},
		{
			name: "subjid",
			role: "A",
			isW: true,
		},
		{
			name: "siteid",
			role: "Y",
			isW: true,
		},
	]
  },
  computed: {

  }
})