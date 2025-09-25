class Job < ApplicationRecord
  validates :title, presence: true
  validates :company, presence: true
  validates :source, presence: true

  enum status: {
    active: 0,
    applied: 1,
    rejected: 2,
    interview: 3,
    offer: 4,
    closed: 5
  }

  enum employment_type: {
    full_time: 0,
    part_time: 1,
    contract: 2,
    internship: 3,
    temporary: 4
  }

  enum experience_level: {
    entry: 0,
    mid: 1,
    senior: 2,
    executive: 3
  }

  scope :recent, -> { order(created_at: :desc) }
  scope :by_company, ->(company) { where(company: company) }
  scope :by_location, ->(location) { where("location ILIKE ?", "%#{location}%") }
  scope :by_title, ->(title) { where("title ILIKE ?", "%#{title}%") }

  def self.create_from_scrape(job_data)
    create!(
      title: job_data[:title],
      company: job_data[:company],
      location: job_data[:location],
      description: job_data[:description],
      url: job_data[:url],
      source: job_data[:source] || 'linkedin',
      external_id: extract_job_id_from_url(job_data[:url]),
      scraped_at: job_data[:scraped_at] || Time.current
    )
  end

  private

  def self.extract_job_id_from_url(url)
    return nil unless url.present?

    # Extract LinkedIn job ID from URL
    match = url.match(/\/jobs\/view\/(\d+)/)
    match ? match[1] : nil
  end
end