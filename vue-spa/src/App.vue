<template>
  <div id="app">
    <input
      type="text"
      name="permissions"
      id="permissions"
      list="permissions-suggestion"
      v-model="selectedPermission"
    />
    <datalist id="permissions-suggestion">
      <option
        v-for="permission in permissionsSuggestion"
        :value="permission.name"
        v-bind:key="permission.id"
      >
      </option>
    </datalist>
    <select
      id="context"
      v-model="context"
      v-on:change="changeContext"
    >
      <option value="application">application</option>
      <option value="delegated">delegated</option>
    </select>
    <div>
      <table>
        <thead>
          <tr>
            <th width="15%">name</th>
            <th width="20%">displayString</th>
            <th width="55%">description</th>
            <th width="10%">Admin Consent</th>
            <th width="10%">MSA supported</th>
          </tr>
        </thead>
        <tbody v-if="selectedPermissionDetail">
          <tr>
            <td>{{selectedPermissionDetail.name}}</td>
            <td>{{selectedPermissionDetail.displayString}}</td>
            <td>{{selectedPermissionDetail.description}}</td>
            <td>{{selectedPermissionDetail.needAdminConsent}}</td>
            <td>{{selectedPermissionDetail.isMsaSupported}}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div>
      <table>
        <thead>
          <tr>
            <th width="15%">name</th>
            <th width="65%">description</th>
            <th width="10%">application permissions</th>
            <th width="10%">delegated permissions</th>
            <th>msa</th>
          </tr>
        </thead>
        <tbody v-if="apiPermission">
          <tr v-for="p in apiPermission" v-bind:key="p.key">
            <td>
              <a :href="p.sourceUri" target="_blank" rel="noopener">{{p.name}}</a>
            </td>
            <td>{{p.description}}</td>
            <td>
              <ul>
                <li v-for="p in p.permissions.application" :key="p">{{p}}</li>
              </ul>
            </td>
            <td>
              <ul>
                <li v-for="p in p.permissions.delegated" :key="p">{{p}}</li>
              </ul>
            </td>
            <td>
              <ul>
                <li v-for="p in p.permissions.msa" :key="p">{{p}}</li>
              </ul>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <table>
      <thead></thead>
      <tbody>
        <tr></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as data from "./api.json";
import * as permissions from "./permissions.json";

export default {
  name: "app",
  data() {
    return {
      selectedPermission: "User.Read.All",
      context: "application",
      permissionsSuggestion: permissions.filter(p => p.type === "application")
    };
  },
  methods: {
    changeContext: function(key){
      console.log(this.context)
      this.permissionsSuggestion = permissions.filter(p => p.type === this.context)
      console.log(this.permissionsSuggestion)
    }
  },
  computed: {
    apiPermission: function() {
      var apiPerm = data.filter(
        api =>
          api.permissions &&
          api.permissions[this.context] &&
          api.permissions[this.context].indexOf(this.selectedPermission) !== -1
      );
      return apiPerm;
    },
    selectedPermissionDetail: function() {
      const pId = this.context + "_" + this.selectedPermission
      return this.permissionsSuggestion.filter(p => p.id === pId)[0];
    }
  }
};
</script>

<style>
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

h1,
h2 {
  font-weight: normal;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  display: inline-block;
  margin: 0 10px;
}

a {
  color: #42b983;
}
</style>
