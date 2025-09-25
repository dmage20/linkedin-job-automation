require_relative "boot"

require "rails/all"

Bundler.require(*Rails.groups)

module LinkedinJobAutomation
  class Application < Rails::Application
    config.load_defaults 7.0

    # CORS configuration
    config.middleware.insert_before 0, Rack::Cors do
      allow do
        origins 'http://localhost:3000'
        resource '*',
          headers: :any,
          methods: [:get, :post, :put, :patch, :delete, :options, :head],
          credentials: true
      end
    end

    # API-only configuration
    config.api_only = false

    # GraphQL configuration
    config.autoload_paths << Rails.root.join('app/graphql')

    # Background jobs
    config.active_job.queue_adapter = :sidekiq
  end
end