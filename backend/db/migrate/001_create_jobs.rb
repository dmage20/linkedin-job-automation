class CreateJobs < ActiveRecord::Migration[7.0]
  def change
    create_table :jobs do |t|
      t.string :title, null: false
      t.string :company, null: false
      t.text :description
      t.string :location
      t.string :url
      t.string :source, null: false, default: 'linkedin'
      t.string :external_id
      t.integer :status, default: 0
      t.integer :employment_type
      t.integer :experience_level
      t.string :salary_min
      t.string :salary_max
      t.string :currency, default: 'USD'
      t.boolean :remote_work, default: false
      t.text :requirements
      t.text :benefits
      t.integer :applicant_count
      t.datetime :posted_at
      t.datetime :scraped_at
      t.float :match_score
      t.text :analysis_notes

      t.timestamps
    end

    add_index :jobs, :external_id
    add_index :jobs, :company
    add_index :jobs, :location
    add_index :jobs, :source
    add_index :jobs, :status
    add_index :jobs, :created_at
  end
end