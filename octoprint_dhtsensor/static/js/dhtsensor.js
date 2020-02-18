$(function() {
  function DHTSensorViewModel() {
    var self = this;

    self.enable = ko.observable(true);

    self.refreshVisible = ko.observable(true);

    self.rawHumidity = ko.observable(-1);
    self.rawTemperature = ko.observable(-1);

    self.decimals = ko.observable(-1);

    self.maxHumidity = ko.observable(-1);
    self.maxTemperature = ko.observable(-1);

    self.humidity = ko.pureComputed(function() {
      var rawHumidity = this.rawHumidity();
      var decimals = this.decimals();

      if (rawHumidity < 0 || decimals < 0) {
        return '';
      }

      return (new Decimal(rawHumidity)
              .div(Math.pow(10, decimals))
              .toFixed(decimals));
    }, self).extend({
      deferred: true
    });

    self.temperature = ko.pureComputed(function() {
      var rawTemperature = this.rawTemperature();
      var decimals = this.decimals();

      if (rawTemperature < 0 || decimals < 0) {
        return '';
      }

      return (new Decimal(rawTemperature)
              .div(Math.pow(10, decimals))
              .toFixed(decimals));
    }, self).extend({
      deferred: true
    });

    self.humidityTooHigh = ko.pureComputed(function() {
      var humidity = this.humidity();
      var maxHumidity = this.maxHumidity();

      if (!humidity || maxHumidity < 0) {
        return false;
      }

      return (new Decimal(humidity).gt(maxHumidity));
    }, self).extend({
      deferred: true
    });

    self.temperatureTooHigh = ko.pureComputed(function() {
      var temperature = this.temperature();
      var maxTemperature = this.maxTemperature();

      if (!temperature || maxTemperature < 0) {
        return false;
      }

      return (new Decimal(temperature).gt(maxTemperature));
    }, self).extend({
      deferred: true
    });

    self.requestRefresh = function() {
      $.ajax({
        url: API_BASEURL + 'plugin/dhtsensor',
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify({
            command: 'refresh'
        }),
        contentType: 'application/json; charset=UTF-8'
      });
    };

    self.onStartup = function() {
      var dhtSensorTab = $('#sidebar_plugin_dhtsensor');

      dhtSensorTab.on('show', function() {
        self.refreshVisible(true);
      });

      dhtSensorTab.on('hide', function() {
        self.refreshVisible(false);
      });

      self.requestRefresh();
    };

    self.onDataUpdaterPluginMessage = function(plugin, data) {
      if (plugin !== 'dhtsensor' || typeof data !== 'object' || !data) {
        return;
      }

      if (data.hasOwnProperty('humidity')) {
        self.rawHumidity(data.humidity);
      }

      if (data.hasOwnProperty('temperature')) {
        self.rawTemperature(data.temperature);
      }

      if (data.hasOwnProperty('enable')) {
        self.enable(data.enable);
      }

      if (data.hasOwnProperty('decimals')) {
        self.decimals(data.decimals);
      }

      if (data.hasOwnProperty('maxHumidity')) {
        self.maxHumidity(data.maxHumidity);
      }

      if (data.hasOwnProperty('maxTemperature')) {
        self.maxTemperature(data.maxTemperature);
      }
    };
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: DHTSensorViewModel,
    elements: ['#sidebar_plugin_dhtsensor_wrapper']
  });
});
